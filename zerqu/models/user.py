# coding: utf-8

import time
import datetime
import hashlib
from flask import request, session, current_app
from werkzeug.urls import url_encode
from werkzeug.local import LocalProxy
from werkzeug.utils import cached_property
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer
from sqlalchemy.orm.attributes import get_history
from flask_oauthlib.utils import to_bytes
from .base import db, cache, Base
from ..libs.utils import Empty

__all__ = ['current_user', 'User', 'AuthSession']


class User(Base):
    __tablename__ = 'zq_user'

    ROLE_SUPER = 9
    ROLE_ADMIN = 8
    ROLE_STAFF = 7
    ROLE_VERIFIED = 4
    ROLE_SPAMMER = -9

    id = Column(Integer, primary_key=True)
    username = Column(String(24), unique=True)
    email = Column(String(255), unique=True)
    _avatar_url = Column('avatar_url', String(260))
    _password = Column('password', String(100))
    description = Column(String(280))

    role = Column(SmallInteger, default=0)
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
            'label', 'reputation', 'is_active',
            'created_at', 'updated_at',
        )

    @cached_property
    def is_active(self):
        return self.role > 0

    @cached_property
    def label(self):
        if self.role >= self.ROLE_STAFF:
            return 'staff'
        if self.role == self.ROLE_VERIFIED:
            return 'verified'
        if self.role == self.ROLE_SPAMMER:
            return 'spammer'
        return None

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
        md5email = hashlib.md5(to_bytes(self.email)).hexdigest()
        params = current_app.config['GRAVATAR_PARAMETERS']
        url = current_app.config['GRAVATAR_URL']
        return '%s%s?%s' % (url, md5email, url_encode(params or {}))

    @avatar_url.setter
    def avatar_url(self, url):
        self._avatar_url = url


@event.listens_for(User, 'after_update')
def receive_user_after_update(mapper, conn, target):
    if target not in db.session.dirty:
        return

    to_delete = []

    prefix = target.generate_cache_prefix('ff')
    for key in ['username', 'email']:
        state = get_history(target, key)
        for value in state.deleted:
            to_delete.append('%s%s$%s' % (prefix, key, value))

    if to_delete:
        cache.delete_many(*to_delete)


class AuthSession(Base):
    __tablename__ = 'zq_auth_session'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=0)

    platform = Column(String(20))
    browser = Column(String(40))

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, default=datetime.datetime.utcnow)

    def __str__(self):
        return u'%s / %s (%d)' % (self.browser, self.platform, self.user_id)

    def keys(self):
        return (
            'id', 'platform', 'browser', 'user',
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
        with db.auto_commit():
            db.session.add(data)
        session['id'] = data.id
        session['ts'] = int(time.time())
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
        with db.auto_commit():
            db.session.delete(data)
        return True

    @classmethod
    def get_current_user(cls):
        """Get current authenticated user."""
        sid = session.get('id')
        if not sid:
            return None

        ts = session.get('ts')
        if ts and int(time.time()) - ts > 300:
            data = cls.query.get(sid)
            if data:
                data.last_used = datetime.datetime.utcnow()
                with db.auto_commit():
                    db.session.add(data)
        else:
            data = cls.cache.get(sid)
        if not data or not data.is_valid():
            session.pop('id', None)
            session.pop('ts', None)
            return None
        return data.user


class Anonymous(Empty):
    id = None

    def __str__(self):
        return "Anonymous User"

    def __repr__(self):
        return "<User: Anonymous>"

ANONYMOUS = Anonymous()


def _get_current_user():
    user = getattr(request, '_current_user', None)
    if user:
        return user
    user = AuthSession.get_current_user()
    if user is None:
        return ANONYMOUS
    request._current_user = user
    return user


current_user = LocalProxy(_get_current_user)
