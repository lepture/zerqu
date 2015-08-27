# coding: utf-8


def register_base(app):
    from flask import request
    from flask_babel import Babel

    from .models import db, social, auth
    from .libs import cache, ratelimit
    from .libs.pigeon import mail
    from .libs.uploader import uploader
    from .models.binds import bind_events

    db.init_app(app)
    social.init_app(app)
    auth.bind_oauth(app)
    cache.init_app(app)
    mail.init_app(app)
    ratelimit.init_app(app)
    uploader.init_app(app)
    bind_events()

    babel = Babel(app)
    supported_locales = app.config.get('BABEL_LOCALES', ['en'])

    @babel.localeselector
    def choose_locale():
        return request.accept_languages.best_match(supported_locales)


def register_base_blueprints(app):
    from .handlers import session, oauth, account

    from .api import init_app
    init_app(app)

    app.register_blueprint(oauth.bp, url_prefix='/oauth')
    app.register_blueprint(session.bp, url_prefix='/session')
    app.register_blueprint(account.bp, url_prefix='/account')


def register_app_blueprints(app):
    from .handlers import front, feeds

    app.register_blueprint(feeds.bp, url_prefix='')
    app.register_blueprint(front.bp, url_prefix='')


def register_not_found(app):
    from flask import request
    from .libs.errors import NotFound

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith('/api/'):
            return NotFound('URL')
        return e


def create_app(config=None):
    from .app import create_app
    app = create_app(config)
    register_base(app)
    register_base_blueprints(app)
    register_app_blueprints(app)
    register_not_found(app)
    return app
