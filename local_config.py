import os


SECRET_KEY = 'secret'

if os.path.isfile('/.dockerenv'):
    is_docker = True
else:
    is_docker = False

if is_docker:
    DB_CONN = 'postgres:secret@db'
else:
    DB_CONN = 'postgres@localhost'

SQLALCHEMY_DATABASE_URI = 'postgresql://{conn}/development'.format(conn=DB_CONN)
SQLALCHEMY_NATIVE_UNICODE = False

if is_docker:
    REDIS_HOST = 'redis'
else:
    REDIS_HOST = 'localhost'
ZERQU_REDIS_URI = 'redis://{}:6379/0'.format(REDIS_HOST)
ZERQU_CACHE_REDIS_HOST = REDIS_HOST

DEBUG = True
