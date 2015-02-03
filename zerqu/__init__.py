# coding: utf-8


def register_model(app):
    from .models import db, CacheClient
    from .models.auth import bind_oauth

    db.init_app(app)
    bind_oauth(app)
    CacheClient(app)


def register_blueprints(app):
    from .handlers import front, session, oauth
    app.register_blueprint(oauth.bp, url_prefix='/oauth')
    app.register_blueprint(session.bp, url_prefix='/session')
    app.register_blueprint(front.bp, url_prefix='')


def create_app(config=None):
    from .app import create_app
    app = create_app(config)
    register_model(app)
    register_blueprints(app)
    return app
