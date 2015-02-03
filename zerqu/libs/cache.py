# coding: utf-8

from redis import Redis
from flask import current_app
from werkzeug.local import LocalProxy


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
