# coding: utf-8

from flask import current_app
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
    return current_app.extensions[prefix + '_redis']


cache = LocalProxy(use_cache)
redis = LocalProxy(use_redis)
