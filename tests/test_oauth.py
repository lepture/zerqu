# coding: utf-8

from werkzeug import url_encode
from zerqu.models import User, AuthSession, OAuthClient
from ._base import TestCase


class TestOAuth(TestCase):

    def login(self):
        user = User.query.first()
        with self.app.test_request_context():
            AuthSession.login(user)

        with self.client.session_transaction() as sess:
            sess['id'] = user.id
        return user

    def test_get_authorize(self):
        rv = self.client.get('/oauth/authorize')
        assert 'invalid_client_id' in rv.location

        client = self.client
        rv = client.get('/oauth/authorize?client_id=ios&response_type=code')
        assert rv.status_code == 200

        user = self.login()

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

    def test_post_authorize(self):
        client_id = OAuthClient.query.first().client_id

        rv = self.client.post('/oauth/authorize', data={
            'client_id': client_id,
            'response_type': 'code',
            'scope': 'user:email',
        })
        assert rv.status_code == 302

        self.login()
        rv = self.client.post('/oauth/authorize', data={
            'client_id': client_id,
            'response_type': 'code',
            'scope': 'user:email',
            'confirm': 'yes',
        })
        assert 'code' not in rv.location

        self.app.config.update({'WTF_CSRF_ENABLED': False})
        rv = self.client.post('/oauth/authorize', data={
            'client_id': client_id,
            'response_type': 'code',
            'scope': 'user:email',
            'confirm': 'yes',
        })
        assert 'code' in rv.location

        rv = self.client.post('/oauth/authorize', data={
            'client_id': client_id,
            'response_type': 'code',
            'scope': 'user:email',
            'confirm': 'no',
        })
        assert 'denied' in rv.location

    def test_access_token(self):
        c = OAuthClient.query.first()

        self.login()
        self.app.config.update({'WTF_CSRF_ENABLED': False})
        rv = self.client.post('/oauth/authorize', data={
            'client_id': c.client_id,
            'response_type': 'code',
            'scope': 'user:email',
            'confirm': 'yes',
        })
        assert 'code' in rv.location
        _, code = rv.location.split('code=', 1)

        rv = self.client.post('/oauth/token', data={
            'client_id': c.client_id,
            'client_secret': c.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': c.default_redirect_uri,
            'code': code,
        })
        assert b'access_token' in rv.data

    def test_errors(self):
        rv = self.client.get('/oauth/errors?error=foo')
        assert b'foo' in rv.data
