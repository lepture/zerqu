# coding: utf-8


import re
from .base import headers_hook
from . import front, user, users, cafes, topics

VERSION_URL = re.compile(r'^/api/\d/')
VERSION_ACCEPT = re.compile(r'application/vnd\.zerqu\+json;\s+version=(\d)')
CURRENT_VERSION = '1'


def find_version(environ):
    accept = environ.get('HTTP_ACCEPT')
    if not accept:
        return CURRENT_VERSION
    rv = VERSION_ACCEPT.findall(accept)
    if rv:
        return rv[0]
    return CURRENT_VERSION


class ApiVersionMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO')
        if not path.startswith('/api/'):
            return self.app(environ, start_response)
        if VERSION_URL.match(path):
            return self.app(environ, start_response)

        version = find_version(environ)
        environ['PATH_INFO'] = path.replace('/api/', '/api/%s/' % version)
        return self.app(environ, start_response)


def register_blueprint(app, bp, name=''):
    bp.after_request(headers_hook)
    url_prefix = '/api/1/' + name
    app.register_blueprint(bp, url_prefix=url_prefix)


def init_app(app):
    app.wsgi_app = ApiVersionMiddleware(app.wsgi_app)
    register_blueprint(app, front.bp, '')
    register_blueprint(app, user.bp, 'user')
    register_blueprint(app, users.bp, 'users')
    register_blueprint(app, cafes.bp, 'cafes')
    register_blueprint(app, topics.bp, 'topics')
