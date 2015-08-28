# coding: utf-8

import time
import hmac
import hashlib
from flask import json
from base64 import urlsafe_b64encode
from werkzeug.security import gen_salt


class Qiniu(object):
    FORM_NAME = 'file'
    CONTENT_TYPES = ('image/jpg', 'image/jpeg', 'image/png')

    TRANSFORM_THUMBNAIL = (
        'imageMogr/v2/auto-orient/thumbnail/1024x>'
    )

    TRANSFORM_COVER = (
        'imageMogr/v2/auto-orient/thumbnail/!1440x600r/'
        'gravity/center/crop/1440x600'
    )

    def __init__(self, app):
        app.config.setdefault('QINIU_EXPIRES', 3600)
        self.access_key = app.config.get('QINIU_ACCESS_KEY')
        self.secret_key = app.config.get('QINIU_SECRET_KEY')
        self.bucket = app.config.get('QINIU_BUCKET')
        self.prefix = app.config.get('QINIU_PREFIX')
        self.expires = app.config.get('QINIU_EXPIRES')
        self.base_url = app.config.get('QINIU_BASE_URL')

    def generate_filename(self, user_id, content_type):
        folder = format(user_id, 'x')
        timestamp = format(int(time.time()), 'x')
        salt = gen_salt(5)
        name = '{}/{}-{}'.format(folder, timestamp, salt)
        if self.prefix:
            name = '{}/{}'.format(self.prefix, name)
        if content_type in ('image/jpg', 'image/jpeg'):
            return name + '.jpg'
        return name + '.png'

    def create_token(self, filename, **data):
        deadline = int(time.time()) + self.expires
        data.update({
            'scope': '%s:%s' % (self.bucket, filename),
            'deadline': deadline,
        })
        data = json.dumps(data)
        encoded_data = urlsafe_b64encode(data)
        signature = hmac.new(self.secret_key, encoded_data, hashlib.sha1)
        encoded_signature = urlsafe_b64encode(signature.digest())
        return '%s:%s:%s' % (
            self.access_key, encoded_signature, encoded_data
        )

    def create_form_data(self, user_id, content_type):
        if content_type not in self.CONTENT_TYPES:
            return None

        filename = self.generate_filename(user_id, content_type)
        # TODO: choose transform type
        transform = self.TRANSFORM_THUMBNAIL

        token = self.create_token(filename, transform=transform)
        return {
            'action': 'https://up.qbox.me',
            'name': self.FORM_NAME,
            'payload': {
                'token': token,
                'key': filename,
            },
            'value': self.base_url + filename,
        }


class Uploader(object):
    def __init__(self, app=None):
        self.service = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        # TODO: add more services
        self.service = Qiniu(app)

    def create_form_data(self, user_id, content_type):
        return self.service.create_form_data(user_id, content_type)

uploader = Uploader()
