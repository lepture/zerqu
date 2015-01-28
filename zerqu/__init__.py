# coding: utf-8

import os
from flask import Flask


def create_flask(config=None):
    app = Flask(__name__)

    #: load default configuration
    app.config.from_object('zerqu.settings')

    #: load environment configuration
    if 'ZERQU_CONF' in os.environ:
        app.config.from_envvar('ZERQU_CONF')

    #: load app sepcified configuration
    if config is not None and isinstance(config, dict):
        app.config.update(config)

    return app


def register_model(app):
    from .models import db
    from .models.auth import bind_oauth

    db.init_app(app)
    bind_oauth(app)


def register_blueprints(app):
    from .handlers import oauth
    app.register_blueprint(oauth.bp, url_prefix='/oauth')


def create_app(config=None):
    app = create_flask(config)
    register_model(app)
    register_blueprints(app)
    return app
