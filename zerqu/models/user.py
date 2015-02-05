# coding: utf-8

import time
import datetime
import hashlib
from flask import request, session, current_app
from werkzeug import url_encode
from werkzeug.local import LocalProxy
from werkzeug.utils import cached_property
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer
from .base import db, cache, Base, CACHE_TIMES

__all__ = ['current_user', 'User', 'AuthSession']


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


def _get_current_user():
    if hasattr(request, '_current_user'):
        return request._current_user
    user = AuthSession.get_current_user()
    request._current_user = user
    return user


current_user = LocalProxy(_get_current_user)
