# coding: utf-8

from functools import wraps
from contextlib import contextmanager
from flask import current_app, g
from werkzeug.local import LocalProxy

# defined time durations
ONE_DAY = 86400
ONE_HOUR = 3600
FIVE_MINUTES = 300


def init_app(app):
    from redis import StrictRedis
    from flask_oauthlib.contrib.cache import Cache

    # register zerqu_cache
    Cache(app, config_prefix='ZERQU')

    # register zerqu_redis
    client = StrictRedis.from_url(app.config['ZERQU_REDIS_URI'])
    app.extensions['zerqu_redis'] = client


def use_cache(prefix='zerqu'):
    return current_app.extensions[prefix + '_cache']


def use_redis(prefix='zerqu'):
    key = prefix + '_redis'
    d = getattr(g, key, None)
    if d is not None:
        return d
    return current_app.extensions[key]


@contextmanager
def execute_pipeline(prefix='zerqu'):
    key = prefix + '_redis'
    redis = current_app.extensions[key]
    with redis.pipeline() as pipe:
        setattr(g, key, pipe)
        yield
        delattr(g, key)
        pipe.execute()


cache = LocalProxy(use_cache)
redis = LocalProxy(use_redis)


def cached(key_pattern, expire=ONE_HOUR):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if '%s' in key_pattern and args:
                key = key_pattern % args
            elif '%(' in key_pattern and kwargs:
                key = key_pattern % kwargs
            else:
                key = key_pattern
            rv = cache.get(key)
            if rv:
                return rv
            rv = f(*args, **kwargs)
            cache.set(key, rv, timeout=expire)
            return rv
        return decorated
    return wrapper
