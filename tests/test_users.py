# coding: utf-8

import base64
from flask import json
from zerqu.models import User


def b64encode(text):
    # TODO: compatible
    return base64.b64encode(text)

auth_header = {
    'Authorization': 'Basic %s' % b64encode('ios:secret')
}


def test_create_user_forbidden(client):
    rv = client.post('/api/user')
    assert rv.status_code == 403


def test_create_user_success(client):
    rv = client.post('/api/user', data=json.dumps({
        'username': 'createuser',
        'email': 'createuser@gmail.com',
        'password': 'test-password',
    }), content_type='application/json', headers=auth_header)
    assert rv.status_code == 201
    data = json.loads(rv.data)
    user = User.cache.filter_first(username='createuser')
    expected = {'status': 'ok', 'data': dict(user)}
    assert data == json.loads(json.dumps(expected))

    # can't register with the same email address
    rv = client.post('/api/user', data=json.dumps({
        'username': 'createuser2',
        'email': 'createuser@gmail.com',
        'password': 'test-password',
    }), content_type='application/json', headers=auth_header)
    assert rv.status_code == 400
    assert b'error_form' in rv.data


def test_create_user_error_form(client):
    rv = client.post('/api/user', data=json.dumps({
        'username': 'createuser',
        'password': 'test-password',
    }), content_type='application/json', headers=auth_header)
    assert rv.status_code == 400
    assert b'error_form' in rv.data

    rv = client.post('/api/user', data=json.dumps({
        'username': 'zerqu',
        'password': 'test-password',
    }), content_type='application/json', headers=auth_header)
    assert rv.status_code == 400
    assert b'registered' in rv.data


def test_current_authenticated_user(client):
    rv = client.get('/api/user')
    assert rv.status_code == 401
