# coding: utf-8

from redis import Redis
from sqlalchemy.orm import Query
from flask import current_app, abort
from werkzeug.local import LocalProxy
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RedisClient(Redis):
    def __init__(self, prefix='ZERQU', app=None):
        self.prefix = prefix
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        config = app.config
        prefix = self.prefix.upper()
        host = config.get(prefix + '_REDIS_HOST', 'localhost')
        port = config.get(prefix + '_REDIS_PORT', 6379)
        db = config.get(prefix + '_REDIS_DB', 0)
        password = config.get(prefix + '_REDIS_PASSWORD', None)
        super(RedisClient, self).__init__(
            host=host, port=port, db=db, password=password
        )
        app.extensions[self.prefix.lower() + '_redis_cache'] = self


def use_redis(prefix='zerqu'):
    return current_app.extensions[prefix + '_redis_cache']


# default redis cache
redis = LocalProxy(use_redis)


class CacheQuery(Query):
    def get_from_cache(self, ident, abort_code=None):
        mapper = self._only_full_mapper_zero('get')
        key = 'sql:%s:%s' % (mapper.mapped_table.name, str(ident))
        rv = redis.get(key)
        if rv:
            return rv
        rv = self.get(ident)
        if rv is not None:
            redis.set(key, rv, 600)
            return rv
        if abort_code:
            abort(abort_code)
        return None


class Base(db.Model):
    __abstract__ = True
    query_class = CacheQuery

    def __getitem__(self, key):
        return getattr(self, key)
