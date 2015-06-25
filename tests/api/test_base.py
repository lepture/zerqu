# coding: utf-8

from zerqu.versions import API_VERSION
from zerqu.models import db, User, OAuthToken
from sqlalchemy.exc import IntegrityError
from flask_oauthlib.utils import to_bytes
from ._base import TestCase


class TestAPI(TestCase):
    def test_get_api_index(self):
        rv = self.client.get('/api/')
        assert to_bytes(API_VERSION) in rv.data


class TestModel(TestCase):
    def test_model_events(self):
        user = User(username='hello', email='hello@gmail.com')
        db.session.add(user)
        db.session.commit()

        # get from database
        assert user == User.cache.get(user.id)
        # get from cache
        cached_user = User.cache.get(user.id)
        assert user != cached_user
        assert user.id == cached_user.id
        assert User.cache.filter_first(username='hello') is not None

        # update cache
        user.username = 'jinja'
        db.session.add(user)
        db.session.commit()
        assert User.cache.get(user.id).username == 'jinja'
        assert User.cache.filter_first(username='hello') is None

        # delete cache
        db.session.delete(user)
        db.session.commit()
        assert User.cache.get(user.id) is None

    def test_get_many_dict(self):
        assert User.cache.get_dict([]) == {}

        for i in range(10):
            user = User(username='foo-%d' % i, email='foo-%d@gmail.com' % i)
            db.session.add(user)
        db.session.commit()

        first_id = User.cache.filter_first(username='foo-0').id
        idents = [first_id + i for i in range(10)]
        missed = User.cache.get_dict(idents)
        assert len(missed.keys()) == 10

        cached = User.cache.get_dict(idents)
        assert list(missed.keys()).sort() == list(cached.keys()).sort()

        missed_names = [o.username for o in missed.values()]
        cached_names = [o.username for o in User.cache.get_many(idents)]
        assert missed_names.sort() == cached_names.sort()

    def test_filter_count(self):
        b1 = User.cache.filter_count()
        b2 = User.cache.filter_count(reputation=0)
        for i in range(10):
            user = User(username='foo-%d' % i, email='foo-%d@gmail.com' % i)
            db.session.add(user)
        db.session.commit()
        a1 = User.cache.filter_count()
        a2 = User.cache.filter_count(reputation=0)
        # will auto clean cache
        assert a1 > b1
        # will not clean cache
        assert a2 == b2


class TestOAuthTokenModel(TestCase):
    def test_oauth_token(self):
        tok = OAuthToken(
            access_token='double',
            token_type='Bearer',
            scope='',
            expires_in=3600,
        )
        tok.user_id = 1
        tok.client_id = 2
        db.session.add(tok)
        db.session.commit()

        assert OAuthToken.query.get((2, 1)) is not None
        assert OAuthToken.query.get((1, 2)) is None

        tok = OAuthToken(
            access_token='double2',
            token_type='Bearer',
            scope='',
            expires_in=3600,
        )
        tok.user_id = 1
        tok.client_id = 2
        db.session.add(tok)
        self.assertRaises(IntegrityError, db.session.commit)
