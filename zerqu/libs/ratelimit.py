# coding: utf-8

import time
import logging
from .cache import cache


logger = logging.getLogger('zerqu')


class Ratelimiter(object):
    def __init__(self, db):
        self.db = db

    def get_data(self):
        return self.db.get_many(self.count_key, self.reset_key)

    def create(self, remaining, expires_at, duration):
        self.db.set_many({
            self.count_key: remaining,
            self.reset_key: expires_at,
        }, duration)

    def remain(self, remaining, expires):
        self.db.set(self.count_key, remaining, expires)

    def __call__(self, prefix, count=600, duration=300):
        logger.info('Rate limit on %s' % prefix)
        self.count_key = '%s$c' % prefix
        self.reset_key = '%s$r' % prefix

        remaining, resetting = self.get_data()
        if not remaining and not resetting:
            remaining = count - 1
            expires_at = duration + int(time.time())
            self.create(remaining, expires_at, duration)
            expires = duration
        else:
            expires = int(resetting) - int(time.time())
            if remaining <= 0 and expires:
                return remaining, expires
            remaining = int(remaining) - 1
            self.remain(remaining, expires)
        return remaining, expires


class RedisRateLimiter(Ratelimiter):
    def get_data(self):
        return self.db.mget(self.count_key, self.reset_key)

    def create(self, remaining, expires_at, duration):
        with self.db.pipeline() as pipe:
            pipe.set(self.count_key, remaining, ex=duration, nx=True)
            pipe.set(self.reset_key, expires_at, ex=duration, nx=True)
            pipe.execute()

    def remain(self, remaining, expires):
        self.db.set(self.count_key, remaining, ex=expires, xx=True)


ratelimit = Ratelimiter(cache)
