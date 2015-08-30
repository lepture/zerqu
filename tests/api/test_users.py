# coding: utf-8

from flask import json
from zerqu.models import db, User, OAuthToken
from ._base import TestCase, encode_base64


auth_header = {
    'Authorization': 'Basic %s' % encode_base64('ios:secret')
}


class TestCreateUser(TestCase):
    def test_create_user_forbidden(self):
        rv = self.client.post('/api/users', headers={
            'X-API-Version': '1',
            'Accept': 'application/vnd.tristram+json; version=2',
        })
        assert rv.status_code == 403

    def test_create_user_success(self):
        rv = self.client.post('/api/users', data=json.dumps({
            'username': 'createuser',
            'email': 'createuser@gmail.com',
            'password': 'test-password',
        }), content_type='application/json', headers=auth_header)
        assert rv.status_code == 201
        data = json.loads(rv.data)
        user = User.cache.filter_first(username='createuser')
        assert data == json.loads(json.dumps(dict(user)))

        # can't register with the same email address
        rv = self.client.post('/api/users', data=json.dumps({
            'username': 'createuser2',
            'email': 'createuser@gmail.com',
            'password': 'test-password',
        }), content_type='application/json', headers=auth_header)
        assert rv.status_code == 400
        assert b'error_form' in rv.data

    def test_create_user_error_form(self):
        rv = self.client.post('/api/users', data=json.dumps({
            'username': 'createuser',
            'password': 'test-password',
        }), content_type='application/json', headers=auth_header)
        assert rv.status_code == 400
        assert b'error_form' in rv.data

        rv = self.client.post('/api/users', data=json.dumps({
            'username': 'zerqu',
            'password': 'test-password',
        }), content_type='application/json', headers=auth_header)
        assert rv.status_code == 400
        assert b'registered' in rv.data


class TestCurrentUser(TestCase):
    def test_current_authenticated_user(self):
        rv = self.client.get('/api/users/me')
        assert rv.status_code == 401

        headers = self.get_authorized_header()
        rv = self.client.get('/api/users/me', headers=headers)
        assert b'username' in rv.data

    def test_update_current_user(self):
        # prepare token
        token = OAuthToken(
            access_token='current-user-access',
            refresh_token='current-user-refresh',
            token_type='Bearer',
            scope='',
            expires_in=3600,
        )
        token.user_id = 1
        token.client_id = 1
        db.session.add(token)
        db.session.commit()

        rv = self.client.patch('/api/users/me', data=json.dumps({
            'description': 'unique_description'
        }), headers={
            'Authorization': 'Bearer current-user-access',
            'Content-Type': 'application/json',
        })
        assert rv.status_code == 401

        token.scope = 'user:write'
        db.session.add(token)
        db.session.commit()

        rv = self.client.patch('/api/users/me', data=json.dumps({
            'description': 'unique_description'
        }), headers={
            'Authorization': 'Bearer current-user-access',
            'Content-Type': 'application/json',
        })
        assert b'unique_description' in rv.data

    def test_update_description(self):
        headers = self.get_authorized_header(user_id=1, scope='user:write')
        rv = self.client.patch('/api/users/me', data=json.dumps({
            'description': 'unique_description'
        }), headers=headers)
        assert b'unique_description' in rv.data

        # request without description
        rv = self.client.patch('/api/users/me', data='{}', headers=headers)
        assert b'unique_description' in rv.data

    def test_current_user_email(self):
        headers = self.get_authorized_header(scope='user:email')
        rv = self.client.get('/api/users/me/email', headers=headers)
        assert b'email' in rv.data


class TestListUsers(TestCase):
    def test_list_without_parameters(self):
        rv = self.client.get('/api/users')
        assert rv.status_code == 200


class TestViewUser(TestCase):
    def test_not_found(self):
        rv = self.client.get('/api/users/not_found')
        assert rv.status_code == 404
        assert b'not_found' in rv.data

    def test_found(self):
        rv = self.client.get('/api/users/zerqu')
        assert rv.status_code == 200

        # change user information
        user = User.query.filter_by(username='zerqu').first()
        user.description = u'changed'
        db.session.add(user)
        db.session.commit()

        cached = self.client.get('/api/users/zerqu')
        assert cached.status_code == 200
        assert rv.data == cached.data


class TestViewUserCafes(TestCase):

    def test_view_user_cafes(self):
        user = User.query.get(1)
        rv = self.client.get(
            '/api/users/%s/cafes' % user.username,
        )
        assert rv.status_code == 200

    def test_view_self_cafes(self):
        user = User.query.get(1)
        headers = self.get_authorized_header(user_id=user.id)
        rv = self.client.get(
            '/api/users/%s/cafes' % user.username,
            headers=headers
        )
        assert rv.status_code == 200


class TestViewUserTopics(TestCase):

    def test_view_user_topics(self):
        user = User.query.get(1)
        rv = self.client.get(
            '/api/users/%s/topics' % user.username,
        )
        assert rv.status_code == 200

    def test_view_self_topics(self):
        user = User.query.get(1)
        headers = self.get_authorized_header(user_id=user.id)
        rv = self.client.get(
            '/api/users/%s/topics' % user.username,
            headers=headers
        )
        assert rv.status_code == 200


class TestUserNotification(TestCase):
    def test_view_notification(self):
        headers = self.get_authorized_header()
        rv = self.client.get(
            '/api/users/me/notification',
            headers=headers
        )
        assert rv.status_code == 200

    def test_clear_notification(self):
        headers = self.get_authorized_header()
        rv = self.client.delete(
            '/api/users/me/notification',
            headers=headers
        )
        assert rv.status_code == 204

    def test_view_notification_count(self):
        headers = self.get_authorized_header()
        rv = self.client.get(
            '/api/users/me/notification/count',
            headers=headers
        )
        assert rv.status_code == 200
