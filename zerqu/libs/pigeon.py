"""
    Sending mails with Pigeon
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Pigeon is a service for sending mails over HTTP.

    https://github.com/lepture/pigeon
"""

import requests
from itsdangerous import json


class Pigeon(object):
    def __init__(self, url=None, secret=None):
        self.url = url
        self.secret = secret

    def init_app(self, app):
        self.url = app.config.get('PIGEON_URL')
        self.secret = app.config.get('PIGEON_SECRET')

    def send(self, user, title, **kwargs):
        if not self.url or not self.secret:
            raise RuntimeError('PIGEON_URL and PIGEON_SECRET are missing')

        kwargs['user'] = user
        kwargs['title'] = title
        payload = json.dumps(kwargs)
        headers = {
            'Content-Type': 'application/json',
            'X-Pigeon-Secret': self.secret,
        }
        return requests.post(self.url, data=payload, headers=headers)

    def send_text(self, user, title, content):
        return self.send(user, title, text=content)

    def send_html(self, user, title, content):
        return self.send(user, title, html=content)


mailer = Pigeon()
