# coding: utf-8

from flask import json
from ._base import TestCase


class TestFrontAPI(TestCase):
    def test_home(self):
        rv = self.client.get('/api/')
        assert rv.status_code == 200

    def test_preview_no_data(self):
        headers = self.get_authorized_header()
        rv = self.client.post('/api/preview', headers=headers)
        assert rv.status_code == 400

        rv = self.client.post('/api/preview', data='{}', headers=headers)
        assert rv.status_code == 200
        assert rv.data == b''

    def test_preview_text(self):
        headers = self.get_authorized_header()
        text = 'hello **world**'
        data = json.dumps({'text': text})
        rv = self.client.post('/api/preview', data=data, headers=headers)
        assert b'<strong>' in rv.data
