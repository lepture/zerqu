
import os
from datetime import datetime
from flask import Flask as _Flask
from flask.json import JSONEncoder as _JSONEncoder


class JSONEncoder(_JSONEncoder):
    def default(self, o):
        if hasattr(o, 'as_dict'):
            return o.as_dict()
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%SZ')
        return JSONEncoder.default(self, o)


class Flask(_Flask):
    json_encoder = JSONEncoder


def create_app(config=None):
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
