# coding: utf-8

from flask import json
from ._base import TestCase


class TestSession(TestCase):
    def test_session_login(self):
        rv = self.client.post('/session', data=json.dumps({
            'username': 'test',
            'password': 'test-password',
        }), content_type='application/json')
        assert rv.status_code == 201
        data = json.loads(rv.data)
        assert data['status'] == 'ok'

        rv = self.client.post('/session', data=json.dumps({
            'username': 'test@gmail.com',
            'password': 'test-password',
        }), content_type='application/json')
        assert rv.status_code == 201
        data = json.loads(rv.data)
        assert data['status'] == 'ok'

        rv = self.client.delete('/session')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'ok'

    def test_session_logout(self):
        rv = self.client.delete('/session')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'error'

    def test_session_login_failed(self):
        rv = self.client.post('/session', data={
            'username': 'test',
            'password': 'test-password',
        })
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'error'

        rv = self.client.post('/session', data=json.dumps({
            'username': 'test',
        }), content_type='application/json')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'error'

        rv = self.client.post('/session', data=json.dumps({
            'password': 'test',
        }), content_type='application/json')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'error'

        rv = self.client.post('/session', data=json.dumps({
            'username': 'test',
            'password': 'test',
        }), content_type='application/json')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'error'
