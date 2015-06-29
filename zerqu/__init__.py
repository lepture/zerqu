# coding: utf-8


def register_model(app):
    from .models import db
    from .models.auth import bind_oauth
    from flask_oauthlib.contrib.cache import Cache

    db.init_app(app)
    bind_oauth(app)
    Cache(app, config_prefix='ZERQU')


def register_base_blueprints(app):
    from .handlers import session, oauth

    from .api import init_app
    init_app(app)

    app.register_blueprint(oauth.bp, url_prefix='/oauth')
    app.register_blueprint(session.bp, url_prefix='/session')


def register_app_blueprints(app):
    from .handlers import front, feeds

    app.register_blueprint(feeds.bp, url_prefix='')
    app.register_blueprint(front.bp, url_prefix='')


def create_app(config=None):
    from .app import create_app
    app = create_app(config)
    register_model(app)
    register_base_blueprints(app)
    return app
