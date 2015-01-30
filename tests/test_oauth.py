# coding: utf-8

from werkzeug import url_encode
from zerqu.models import User, AuthSession, OAuthClient


def login(app, client):
    user = User.query.first()
    with app.test_request_context():
        AuthSession.login(user)

    with client.session_transaction() as sess:
        sess['id'] = user.id
    return user


def test_get_authorize(app):
    client = app.test_client()
    rv = client.get('/oauth/authorize')
    assert 'invalid_client_id' in rv.location

    rv = client.get('/oauth/authorize?client_id=ios&response_type=code')
    assert rv.status_code == 200

    user = login(app, client)

    rv = client.get('/oauth/authorize?client_id=ios&response_type=code')
    assert rv.status_code == 200
    assert user.username in rv.data

    oauth_client = OAuthClient.query.first()

    rv = client.get('/oauth/authorize?%s' % url_encode({
        'client_id': oauth_client.client_id,
        'response_type': 'code',
        'scope': 'user',
    }))
    assert b'user:email' in rv.data
    assert b'user:write' in rv.data

    rv = client.get('/oauth/authorize?%s' % url_encode({
        'client_id': oauth_client.client_id,
        'response_type': 'code',
        'scope': 'user:email',
    }))
    assert b'user:email' in rv.data
    assert b'user:write' not in rv.data


def test_post_authorize(app):
    client_id = OAuthClient.query.first().client_id

    client = app.test_client()
    rv = client.post('/oauth/authorize', data={
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'user:email',
    })
    assert rv.status_code == 302

    login(app, client)
    rv = client.post('/oauth/authorize', data={
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'user:email',
        'confirm': 'yes',
    })
    assert 'code' not in rv.location

    app.config.update({'WTF_CSRF_ENABLED': False})
    rv = client.post('/oauth/authorize', data={
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'user:email',
        'confirm': 'yes',
    })
    assert 'code' in rv.location

    rv = client.post('/oauth/authorize', data={
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'user:email',
        'confirm': 'no',
    })
    assert 'denied' in rv.location


def test_access_token(app):
    client = app.test_client()
    c = OAuthClient.query.first()

    login(app, client)
    app.config.update({'WTF_CSRF_ENABLED': False})
    rv = client.post('/oauth/authorize', data={
        'client_id': c.client_id,
        'response_type': 'code',
        'scope': 'user:email',
        'confirm': 'yes',
    })
    assert 'code' in rv.location
    _, code = rv.location.split('code=', 1)

    rv = client.post('/oauth/token', data={
        'client_id': c.client_id,
        'client_secret': c.client_secret,
        'grant_type': 'authorization_code',
        'redirect_uri': c.default_redirect_uri,
        'code': code,
    })
    assert b'access_token' in rv.data
