
import os
from datetime import datetime
from flask import Flask as _Flask
from flask.json import JSONEncoder as _JSONEncoder
SYSTEM_CONF = '/etc/zerqu/conf.py'


class JSONEncoder(_JSONEncoder):
    def default(self, o):
        if hasattr(o, 'keys') and hasattr(o, '__getitem__'):
            return dict(o)
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%SZ')
        return JSONEncoder.default(self, o)


class Flask(_Flask):
    json_encoder = JSONEncoder
    jinja_options = dict(
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
        ]
    )


def create_app(config=None):
    app = Flask(__name__)

    #: load default configuration
    app.config.from_object('zerqu.settings')

    #: load system configuration
    if os.path.isfile(SYSTEM_CONF):
        app.config.from_pyfile(SYSTEM_CONF)

    #: load environment configuration
    if 'ZERQU_CONF' in os.environ:
        app.config.from_envvar('ZERQU_CONF')

    #: load app sepcified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)
    return app
