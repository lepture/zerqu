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

    rv = client.post('/session', data=json.dumps({
        'username': 'test@zerqu',
        'password': 'test-password',
    }), content_type='application/json')
    assert rv.status_code == 201
    data = json.loads(rv.data)
    assert data['status'] == 'ok'

    rv = client.delete('/session')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'ok'


def test_session_logout(app):
    rv = app.test_client().delete('/session')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'error'


def test_session_login_failed(app):
    client = app.test_client()
    rv = client.post('/session', data={
        'username': 'test',
        'password': 'test-password',
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'error'

    rv = client.post('/session', data=json.dumps({
        'username': 'test',
    }), content_type='application/json')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'error'

    rv = client.post('/session', data=json.dumps({
        'password': 'test',
    }), content_type='application/json')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'error'

    rv = client.post('/session', data=json.dumps({
        'username': 'test',
        'password': 'test',
    }), content_type='application/json')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'error'
