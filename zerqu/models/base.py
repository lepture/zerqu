# coding: utf-8

from sqlalchemy.orm import Query
from flask import current_app
from werkzeug.local import LocalProxy
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(session_options={'expire_on_commit': False})


def use_cache(prefix='zerqu'):
    return current_app.extensions[prefix + '_cache']


# default cache
cache = LocalProxy(use_cache)


class CacheQuery(Query):
    def get(self, ident):
        mapper = self._only_full_mapper_zero('get')
        key = 'db:get:%s:%s' % (mapper.mapped_table.name, str(ident))
        rv = cache.get(key)
        if rv:
            return rv
        rv = super(CacheQuery, self).get(ident)
        if rv is None:
            return None
        cache.set(key, rv, 600)
        return rv

    def filter_first(self, **kwargs):
        mapper = self._only_mapper_zero()
        key = '-'.join(['%s$%s' % (k, kwargs[k]) for k in kwargs])
        key = 'db:first:%s:%s' % (mapper.mapped_table.name, key)
        rv = cache.get(key)
        if rv:
            return rv
        rv = self.filter_by(**kwargs).first()
        if rv is None:
            return None
        cache.set(key, rv, 600)
        return rv


class Base(db.Model):
    __abstract__ = True
    query_class = CacheQuery

    def __getitem__(self, key):
        return getattr(self, key)
