# coding: utf-8

import datetime
from werkzeug.utils import cached_property
from werkzeug.security import gen_salt
from sqlalchemy import event
from sqlalchemy import Column
from sqlalchemy import String, DateTime, Boolean, Text, Integer
from flask_oauthlib.provider import OAuth2Provider
from flask_oauthlib.contrib.oauth2 import bind_cache_grant
from .base import db, Base, CACHE_TIMES
from .user import User, AuthSession
from ..libs.cache import cache

__all__ = ['oauth', 'bind_oauth', 'OAuthClient', 'OAuthToken']

oauth = OAuth2Provider()


class OAuthClient(Base):
    __tablename__ = 'zq_oauth_client'

    id = Column(Integer, primary_key=True)

    name = Column(String(40), nullable=False, unique=True)
    avatar_url = Column(String(260))
    description = Column(String(140))

    user_id = Column(Integer, nullable=False, index=True)

    client_id = Column(String(64), unique=True, index=True)
    client_secret = Column(String(64), unique=True, index=True)

    is_confidential = Column(Boolean, default=False)
    default_scope = Column(String(140), default='')
    _redirect_uris = Column('redirect_uris', Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<OAuth Client: %s>' % self.name

    def __str__(self):
        return self.name

    @property
    def user(self):
        return User.cache.get(self.user_id)

    @property
    def default_scopes(self):
        if self.default_scope:
            return self.default_scope.split()
        return []

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        if self.redirect_uris:
            return self.redirect_uris[0]
        return None

    def validate_scopes(self, scopes):
        #: TODO
        return True


@event.listens_for(OAuthClient, 'after_update')
def receive_oauth_client_after_update(mapper, conn, target):
    prefix = target.generate_cache_prefix('ff')
    key = prefix + 'client_id$' + target.client_id
    cache.set(key, target, CACHE_TIMES['ff'])


@event.listens_for(OAuthClient, 'after_delete')
def receive_oauth_client_after_delete(mapper, conn, target):
    prefix = target.generate_cache_prefix('ff')
    key = prefix + 'client_id$' + target.client_id
    cache.delete(key)


class OAuthToken(Base):
    __tablename__ = 'zq_oauth_token'

    client_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=0, primary_key=True)

    access_token = Column(String(34), unique=True, index=True)
    refresh_token = Column(String(34), unique=True, index=True)
    token_type = Column(String(10), default='Bearer')
    scope = Column(String(480), default='')
    expires_in = Column(Integer, default=3600)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, access_token, token_type, scope, expires_in,
                 refresh_token=None, **kwargs):
        self.access_token = access_token
        self.token_type = token_type
        self.scope = scope
        self.expires_in = expires_in
        if refresh_token is None:
            refresh_token = gen_salt(34)
        self.refresh_token = refresh_token

    def keys(self):
        return ('id', 'scopes', 'created_at', 'last_used')

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)

    @cached_property
    def client(self):
        return OAuthClient.cache.get(self.client_id)

    @property
    def expires(self):
        return self.created_at + datetime.timedelta(seconds=self.expires_in)


@event.listens_for(OAuthToken, 'after_update')
def receive_oauth_token_after_update(mapper, conn, target):
    prefix = target.generate_cache_prefix('ff')
    to_cache = {
        prefix + 'access_token$' + target.access_token: target,
        prefix + 'refresh_token$' + target.refresh_token: target,
    }
    cache.set_many(to_cache, CACHE_TIMES['ff'])


@event.listens_for(OAuthToken, 'after_delete')
def receive_oauth_token_after_delete(mapper, conn, target):
    prefix = target.generate_cache_prefix('ff')
    keys = [
        prefix + 'access_token$' + target.access_token,
        prefix + 'refresh_token$' + target.refresh_token,
    ]
    cache.delete_many(keys)


def bind_oauth(app):
    # bind oauth getters and setters
    oauth.init_app(app)

    @oauth.usergetter
    def oauth_user_getter(username, password, *args, **kwargs):
        user = User.cache.filter_first(username=username)
        if user and user.check_password(password):
            return user
        return None

    @oauth.clientgetter
    def oauth_client_getter(client_id):
        return OAuthClient.cache.filter_first(client_id=client_id)

    @oauth.tokengetter
    def oauth_token_getter(access_token=None, refresh_token=None):
        if access_token:
            return OAuthToken.cache.filter_first(access_token=access_token)
        if refresh_token:
            return OAuthToken.cache.filter_first(refresh_token=refresh_token)

    @oauth.tokensetter
    def oauth_token_setter(token, req, *args, **kwargs):
        if hasattr(req, 'user') and req.user:
            user = req.user
        else:
            user = AuthSession.get_current_user()

        client = req.client
        exist_token = OAuthToken.query.get((client.id, user.id))
        if exist_token:
            with db.auto_commit():
                db.session.delete(exist_token)

        tok = OAuthToken(**token)
        tok.user_id = user.id
        tok.client_id = client.id
        with db.auto_commit():
            db.session.add(tok)
        return tok

    # use the same cache
    bind_cache_grant(
        app, oauth,
        AuthSession.get_current_user,
        config_prefix='ZERQU',
    )
