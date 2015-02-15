# coding: utf-8


from .base import ratelimit_hook
from . import front, user, users, cafes


def register_blueprint(app, bp, name=''):
    bp.after_request(ratelimit_hook)
    url_prefix = '/api/' + name
    app.register_blueprint(bp, url_prefix=url_prefix)


def init_app(app):
    register_blueprint(app, front.bp, '')
    register_blueprint(app, user.bp, 'user')
    register_blueprint(app, users.bp, 'users')
    register_blueprint(app, cafes.bp, 'cafes')
