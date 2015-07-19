"""
    Sending mails with Pigeon
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Pigeon is a service for sending mails over HTTP.

    https://github.com/lepture/pigeon
"""

import requests
from flask import current_app
from itsdangerous import json


def send(user, title, **kwargs):
    url = current_app.config.get('PIGEON_URL')
    secret = current_app.config.get('PIGEON_SECRET')
    if not url or secret:
        raise RuntimeError('PIGEON_URL and PIGEON_SECRET are missing')

    kwargs['user'] = user
    kwargs['title'] = title
    payload = json.dumps(kwargs)
    headers = {
        'Content-Type': 'application/json',
        'X-Pigeon-Secret': secret,
    }
    return requests.post(url, data=payload, headers=headers)


def send_text(user, title, content):
    return send(user, title, text=content)


def send_html(user, title, content):
    return send(user, title, html=content)
