
import os
from datetime import datetime
from flask import Flask as _Flask
from flask import request
from flask.json import JSONEncoder as _JSONEncoder

try:
    from raven.contrib.flask import Sentry

    class FlaskSentry(Sentry):
        def before_request(self, *args, **kwargs):
            self.last_event_id = None

        def update_context(self):
            if 'request' not in self.client.context:
                self.client.http_context(self.get_http_info(request))
            if 'user' not in self.client.context:
                self.client.user_context(self.get_user_info(request))

        def get_user_info(self, request):
            from .models import current_user
            if not current_user:
                return
            return {
                'id': current_user.id,
                'username': current_user.username,
            }

        def captureException(self, *args, **kwargs):
            self.update_context()
            super(FlaskSentry, self).captureException(*args, **kwargs)

        def captureMessage(self, *args, **kwargs):
            self.update_context()
            super(FlaskSentry, self).captureMessage(*args, **kwargs)

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
        FlaskSentry(app, logging=False, wrap_wsgi=False)
    return app
