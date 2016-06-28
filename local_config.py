import os


SECRET_KEY = 'secret'
SQLALCHEMY_NATIVE_UNICODE = False
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:secret@postgres/development'
ZERQU_REDIS_URI = 'redis://redis:6379/0'
ZERQU_CACHE_REDIS_HOST = 'redis'

DEBUG = True
