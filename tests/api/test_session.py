# coding: utf-8

import base64
from flask import json
from ._base import TestCase


def encode_auth_headers(username, password):
    code = base64.b64encode(b'%s:%s' % (username, password))
    return {'Authorization': 'Basic %s' % code.decode('utf-8')}


class TestSession(TestCase):
    def test_session_login(self):
        rv = self.client.post(
            '/session',
            data='{}',
            headers=encode_auth_headers('test', 'test-password'),
            content_type='application/json',
        )
        assert rv.status_code == 201
        data = json.loads(rv.data)
        assert data['username'] == 'test'

        rv = self.client.post(
            '/session',
            data='{}',
            headers=encode_auth_headers('test@gmail.com', 'test-password'),
            content_type='application/json',
        )
        assert rv.status_code == 201
        data = json.loads(rv.data)
        assert data['username'] == 'test'

        rv = self.client.delete('/session')
        assert rv.status_code == 204

    def test_session_logout(self):
        rv = self.client.delete('/session')
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert data['status'] == 'error'

    def test_session_login_failed(self):
        rv = self.client.post('/session', data={
            'username': 'test',
            'password': 'test-password',
        })
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert data['status'] == 'error'

        rv = self.client.post('/session', data=json.dumps({
            'username': 'test',
        }), content_type='application/json')
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert data['status'] == 'error'

        rv = self.client.post('/session', data=json.dumps({
            'password': 'test',
        }), content_type='application/json')
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert data['status'] == 'error'

        rv = self.client.post('/session', data=json.dumps({
            'username': 'test',
            'password': 'test',
        }), content_type='application/json')
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert data['status'] == 'error'
