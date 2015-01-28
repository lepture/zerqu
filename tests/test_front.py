# coding: utf-8

import json


def test_session_login(app):
    client = app.test_client()
    rv = client.post('/session', data=json.dumps({
        'username': 'test',
        'password': 'test-password',
    }), content_type='application/json')
    assert rv.status_code == 201
    data = json.loads(rv.data)
    assert data['status'] == 'ok'
