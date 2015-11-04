
from flask import request
from raven.contrib.flask import Sentry
from zerqu.models import current_user


class FlaskSentry(Sentry):
    def before_request(self, *args, **kwargs):
        self.last_event_id = None

    def update_context(self):
        if 'request' not in self.client.context:
            self.client.http_context(self.get_http_info(request))
        if 'user' not in self.client.context:
            self.client.user_context(self.get_user_info(request))

    def get_user_info(self, request):
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
