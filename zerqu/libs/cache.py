
from flask import current_app
from werkzeug.local import LocalProxy


def use_cache(prefix='zerqu'):
    return current_app.extensions[prefix + '_cache']


# default cache
cache = LocalProxy(use_cache)

# defined time durations
ONE_DAY = 86400
ONE_HOUR = 3600
FIVE_MINUTES = 300
