# coding: utf-8

import time
import datetime
import hashlib
from flask import request, session, current_app
from werkzeug import url_encode
from werkzeug.local import LocalProxy
from werkzeug.utils import cached_property
from werkzeug.security import gen_salt
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy import Column
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy import SmallInteger, Integer
from flask_oauthlib.provider import OAuth2Provider
from flask_oauthlib.contrib.oauth2 import bind_sqlalchemy, bind_cache_grant
from .base import db, cache, Base, CACHE_TIMES

__all__ = [
    'oauth', 'bind_oauth', 'current_user',
    'User', 'OAuthClient', 'OAuthToken', 'AuthSession'
]

oauth = OAuth2Provider()


class User(Base):
    __tablename__ = 'zq_user'

    STATUS = {
        0: 'inactive',
        1: 'active',
        2: 'verified',
        8: 'staff',
        9: 'admin',
        10: 'super',
    }
    ROLE_SUPER = 10
    ROLE_ADMIN = 9
    ROLE_STAFF = 8

    id = Column(Integer, primary_key=True)
    username = Column(String(24), unique=True)
    email = Column(String(255), unique=True)
    _avatar_url = Column('avatar_url', String(260))
    _password = Column('password', String(100))
    description = Column(String(280))

    status = Column('status', SmallInteger, default=0)
    reputation = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<User:%s>' % self.username

    def __str__(self):
        return self.username

    def keys(self):
        return (
            'id', 'username', 'avatar_url', 'description',
            'role', 'label', 'reputation', 'is_active',
            'created_at', 'updated_at',
        )

    @cached_property
    def is_active(self):
        return self.status > 0

    @cached_property
    def role(self):
        if self.label == 'staff':
            return 'staff'
        return 'user'

    @cached_property
    def label(self):
        if self.status >= 8:
            return 'staff'
        if self.status == 2:
            return 'verified'
        return 'user'

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, raw):
        self._password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self._password, raw)

    @property
    def avatar_url(self):
        if self._avatar_url:
            return self._avatar_url
        md5email = hashlib.md5(self.email).hexdigest()
        params = current_app.config['GRAVATAR_PARAMETERS']
        url = current_app.config['GRAVATAR_URL']
        return '%s%s?%s' % (url, md5email, url_encode(params or {}))

    @avatar_url.setter
    def avatar_url(self, url):
        self._avatar_url = url


@event.listens_for(User, 'after_update')
def receive_user_after_update(mapper, conn, target):
    prefix = target.generate_cache_prefix('ff')
    to_cache = {
        prefix + 'username$' + target.username: target,
        prefix + 'email$' + target.email: target,
    }
    cache.set_many(to_cache, CACHE_TIMES['ff'])


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


class OAuthToken(Base):
    __tablename__ = 'zq_oauth_token'

    id = Column(Integer, primary_key=True)

    access_token = Column(String(34), unique=True, index=True)
    refresh_token = Column(String(34), unique=True, index=True)
    token_type = Column(String(10), default='Bearer')
    scope = Column(String(480), default='')
    expires_in = Column(Integer, default=3600)

    client_id = Column(String(64), index=True)
    user_id = Column(Integer, default=0, index=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, access_token, token_type, scope, expires_in,
                 refresh_token=None, **kwargs):
        self.access_token = access_token
        self.token_type = token_type
        self.scope = self.scope
        self.expires_in = expires_in
        if refresh_token is None:
            refresh_token = gen_salt(34)
        self.refresh_token = refresh_token

    def keys(self):
        return ('id', 'scopes', 'created_at', 'last_used')

    @cached_property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []


class AuthSession(Base):
    __tablename__ = 'zq_auth_session'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=0)

    ip = Column(String(128))
    platform = Column(String(20))
    browser = Column(String(40))

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, default=datetime.datetime.utcnow)

    def __str__(self):
        return '%s / %s (%d)' % (self.browser, self.platform, self.user_id)

    def keys(self):
        return (
            'id', 'platform', 'browser', 'ip', 'user',
            'created_at', 'last_used',
        )

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)

    def is_valid(self):
        """Verify current session is valid."""
        if not current_app.config.get('ZERQU_VERIFY_SESSION'):
            return True
        ua = request.user_agent
        return (ua.platform, ua.browser) == (self.platform, self.browser)

    @classmethod
    def login(cls, user, permanent=False):
        request._current_user = user
        ua = request.user_agent
        data = cls(
            user_id=user.id,
            platform=ua.platform,
            browser=ua.browser,
        )
        db.session.add(data)
        db.session.commit()
        session['id'] = data.id
        session['ts'] = str(int(time.time()))
        if permanent:
            session.permanent = True
        return data

    @classmethod
    def logout(cls):
        sid = session.pop('id', None)
        if not sid:
            return False
        data = cls.query.get(sid)
        if not data:
            return False
        db.session.delete(data)
        db.session.commit()
        return True

    @classmethod
    def get_current_user(cls):
        """Get current authenticated user."""
        sid = session.get('id')
        if not sid:
            return None
        data = cls.cache.get(sid)
        if not data or not data.is_valid():
            session.pop('id', None)
            session.pop('ts', None)
            return None
        return data.user


def bind_oauth(app):
    # bind oauth getters and setters
    oauth.init_app(app)
    bind_sqlalchemy(
        oauth,
        db.session,
        user=User,
        client=OAuthClient,
        token=OAuthToken,
        current_user=AuthSession.get_current_user,
    )
    bind_cache_grant(app, oauth, AuthSession.get_current_user)


def _get_current_user():
    if hasattr(request, '_current_user'):
        return request._current_user
    user = AuthSession.get_current_user()
    request._current_user = user
    return user


current_user = LocalProxy(_get_current_user)
