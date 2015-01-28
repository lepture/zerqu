# coding: utf-8

import time
import datetime
import hashlib
from flask import request, session, current_app
from werkzeug import url_encode
from werkzeug.utils import cached_property
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy import SmallInteger, Integer
from .base import db, Base


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

    def verify_password(self, raw):
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
        return User.query.get(self.user_id)

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


class OAuthToken(Base):
    __tablename__ = 'zq_oauth_token'

    id = Column(Integer, primary_key=True)

    access_token = Column(String(34), unique=True, index=True)
    refresh_token = Column(String(34), unique=True, index=True)
    token_type = Column(String(10), default='Bearer')
    scope = Column(String(480), default='')
    expires_in = Column(Integer, default=3600)

    client_id = Column(Integer, nullable=False)
    user_id = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, default=datetime.datetime.utcnow)

    @property
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

    @cached_property
    def user(self):
        return User.query.get(self.user_id)

    def is_valid(self):
        """Verify current session is valid."""
        if not current_app.config.get('ZERQU_VERIFY_SESSION'):
            return True
        ua = request.user_agent
        return (ua.platform, ua.browser) == (self.platform, self.browser)

    @classmethod
    def login(cls, user, permanent=False):
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
    def get_current_user(cls):
        """Get current authenticated user."""
        session_id = session.get('id')
        if not session_id:
            return None
        data = cls.query.get(session_id)
        if not data or not data.is_valid():
            session.pop('id', None)
            session.pop('ts', None)
            return None
        return User.query.get(data.user_id)
