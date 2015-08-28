# coding: utf-8

from contextlib import contextmanager

from flask import json
from flask import current_app, abort
from sqlalchemy import event, func
from sqlalchemy.orm import Query, class_mapper
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.dialects.postgresql import JSON as _JSON
from werkzeug.utils import cached_property
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy

from zerqu.libs.utils import is_json
from zerqu.libs.cache import cache, redis, ONE_DAY, FIVE_MINUTES
from zerqu.libs.errors import NotFound

__all__ = ['db', 'CACHE_TIMES', 'Base']

CACHE_TIMES = {
    'get': ONE_DAY,
    'count': ONE_DAY,
    'ff': FIVE_MINUTES,
    'fc': FIVE_MINUTES,
}
CACHE_MODEL_PREFIX = 'db'


class SQLAlchemy(_SQLAlchemy):
    @contextmanager
    def auto_commit(self, throw=True):
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            current_app.logger.exception('%r' % e)
            if throw:
                raise e


db = SQLAlchemy(session_options={
    'expire_on_commit': False,
    'autoflush': False,
})


class CacheQuery(Query):
    def get(self, ident):
        mapper = self._only_full_mapper_zero('get')

        if isinstance(ident, (list, tuple)):
            suffix = '-'.join(map(str, ident))
        else:
            suffix = str(ident)

        key = mapper.class_.generate_cache_prefix('get') + suffix
        rv = cache.get(key)
        if rv:
            return rv
        rv = super(CacheQuery, self).get(ident)
        if rv is None:
            return None
        cache.set(key, rv, CACHE_TIMES['get'])
        return rv

    def get_dict(self, idents):
        if not idents:
            return {}

        mapper = self._only_full_mapper_zero('get')
        if len(mapper.primary_key) != 1:
            raise NotImplemented

        prefix = mapper.class_.generate_cache_prefix('get')
        keys = {prefix + str(i) for i in idents}
        rv = cache.get_dict(*keys)

        missed = {i for i in idents if rv[prefix + str(i)] is None}

        rv = {k.lstrip(prefix): rv[k] for k in rv}

        if not missed:
            return rv

        pk = mapper.primary_key[0]
        missing = self.filter(pk.in_(missed)).all()
        to_cache = {}
        for item in missing:
            ident = str(getattr(item, pk.name))
            to_cache[prefix + ident] = item
            rv[ident] = item

        cache.set_many(to_cache, CACHE_TIMES['get'])
        return rv

    def get_many(self, idents, clean=True):
        d = self.get_dict(idents)
        if clean:
            return list(_itervalues(d, idents))
        return [d[str(k)] for k in idents]

    def filter_first(self, **kwargs):
        mapper = self._only_mapper_zero()
        prefix = mapper.class_.generate_cache_prefix('ff')
        key = prefix + '-'.join(['%s$%s' % (k, kwargs[k]) for k in kwargs])
        rv = cache.get(key)
        if rv:
            return rv
        rv = self.filter_by(**kwargs).first()
        if rv is None:
            return None
        # it is hard to invalidate this cache, expires in 2 minutes
        cache.set(key, rv, CACHE_TIMES['ff'])
        return rv

    def filter_count(self, **kwargs):
        mapper = self._only_mapper_zero()
        model = mapper.class_
        if not kwargs:
            key = model.generate_cache_prefix('count')
            rv = cache.get(key)
            if rv is not None:
                return rv
            q = self.select_from(model).with_entities(func.count(1))
            rv = q.scalar()
            cache.set(key, rv, CACHE_TIMES['count'])
            return rv

        prefix = model.generate_cache_prefix('fc')
        key = prefix + '-'.join(['%s$%s' % (k, kwargs[k]) for k in kwargs])
        rv = cache.get(key)
        if rv:
            return rv
        q = self.select_from(model).with_entities(func.count(1))
        rv = q.filter_by(**kwargs).scalar()
        cache.set(key, rv, CACHE_TIMES['fc'])
        return rv

    def get_or_404(self, ident):
        data = self.get(ident)
        if data:
            return data

        if is_json():
            mapper = self._only_full_mapper_zero('get')
            key = '%s "%r"' % (mapper.class_.__name__, ident)
            raise NotFound(key)
        abort(404)

    def first_or_404(self, **kwargs):
        data = self.filter_first(**kwargs)
        if data:
            return data

        if is_json():
            mapper = self._only_full_mapper_zero('get')
            key = mapper.class_.__name__
            if len(kwargs) == 1:
                key = '%s "%s"' % (key, list(kwargs.values())[0])
            raise NotFound(key)
        abort(404)


class CacheProperty(object):
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, type):
        try:
            mapper = class_mapper(type)
            if mapper:
                return CacheQuery(mapper, session=self.sa.session())
        except UnmappedClassError:
            return None


class BaseMixin(object):
    __reference__ = {}

    def __getitem__(self, key):
        return getattr(self, key)

    @classmethod
    def iter_dict(cls, items, **references):
        for item in items:
            data = dict(item)
            for key in cls.__reference__:
                ident = getattr(item, cls.__reference__[key])
                choices = references.get(key, {})
                data[key] = choices.get(str(ident))
            yield data

    @classmethod
    def generate_cache_prefix(cls, name):
        prefix = '%s:%s:%s' % (CACHE_MODEL_PREFIX, name, cls.__tablename__)
        if hasattr(cls, '__cache_version__'):
            return '%s|%s:' % (prefix, cls.__cache_version__)
        return '%s:' % prefix

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'after_insert')
        def receive_after_insert(mapper, conn, target):
            cache.inc(target.generate_cache_prefix('count'))

        @event.listens_for(cls, 'after_update')
        def receive_after_update(mapper, conn, target):
            key = _unique_key(target, mapper.primary_key)
            cache.set(key, target, CACHE_TIMES['get'])

        @event.listens_for(cls, 'after_delete')
        def receive_after_delete(mapper, conn, target):
            key = _unique_key(target, mapper.primary_key)
            cache.delete_many(key, target.generate_cache_prefix('count'))


class Base(db.Model, BaseMixin):
    __abstract__ = True
    cache = CacheProperty(db)


class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionaries to MutableDict."""
        if isinstance(value, MutableDict):
            return value
        if isinstance(value, dict):
            return MutableDict(value)
        # this call will raise ValueError
        return Mutable.coerce(key, value)

    def __setitem__(self, key, value):
        """Detect dictionary set events and emit change events."""
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        """Detect dictionary del events and emit change events."""
        dict.__delitem__(self, key)
        self.changed()

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        self.update(state)


class JSON(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""
    impl = TEXT

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(_JSON())
        return dialect.type_descriptor(TEXT())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        return json.loads(value)

MutableDict.associate_with(JSON)


def _unique_suffix(target, primary_key):
    return '-'.join(map(lambda k: str(getattr(target, k.name)), primary_key))


def _unique_key(target, primary_key):
    key = _unique_suffix(target, primary_key)
    return target.generate_cache_prefix('get') + key


def _itervalues(data, idents):
    for k in idents:
        item = data[str(k)]
        if item is not None:
            yield item


class RedisStat(object):
    KEY_PREFIX = 'stat:{}'

    def __init__(self, ident):
        self.ident = ident
        self._key = self.KEY_PREFIX.format(ident)

    def increase(self, field, step=1):
        redis.hincrby(self._key, field, step)

    def get(self, key, default=0):
        return self.value.get(key, default)

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, item, value):
        redis.hset(self._key, item, int(value))

    @cached_property
    def value(self):
        return redis.hgetall(self._key)

    @classmethod
    def get_many(cls, ids):
        with redis.pipeline() as pipe:
            for i in ids:
                pipe.hgetall(cls.KEY_PREFIX.format(i))
            return pipe.execute()

    @classmethod
    def get_dict(cls, ids):
        rv = cls.get_many(ids)
        return dict(zip(ids, rv))
