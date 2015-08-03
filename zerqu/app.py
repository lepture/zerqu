
import os
from datetime import datetime
from flask import Flask as _Flask
from flask.json import JSONEncoder as _JSONEncoder

try:
    from raven.contrib.flask import Sentry

    class FlaskSentry(Sentry):
        def get_user_info(self, request):
            from .models import current_user
            if not current_user:
                return
            return dict(current_user)
except ImportError:
    FlaskSentry = None


class JSONEncoder(_JSONEncoder):
    def default(self, o):
        if hasattr(o, 'keys') and hasattr(o, '__getitem__'):
            return dict(o)
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
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    if not app.debug and not app.testing and FlaskSentry:
        FlaskSentry(app)
    return app
