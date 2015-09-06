# coding: utf-8

import time
import uuid
import datetime
from flask import request, session, current_app
from werkzeug.utils import cached_property
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy import Column
from sqlalchemy import String, Unicode, DateTime
from sqlalchemy import SmallInteger, Integer
from sqlalchemy.orm.attributes import get_history
from zerqu.libs.cache import cache, redis
from .base import db, Base

__all__ = ['User', 'UserSession']


class User(Base):
    __tablename__ = 'zq_user'

    ROLE_SUPER = 9
    ROLE_ADMIN = 8
    ROLE_STAFF = 7
    ROLE_VERIFIED = 4
    ROLE_SPAMMER = -9
    ROLE_ACTIVE = 1

    id = Column(Integer, primary_key=True)
    username = Column(String(24), unique=True)
    email = Column(String(255), unique=True)
    _avatar_url = Column('avatar_url', String(260))
    _password = Column('password', String(100))

    name = Column(Unicode(40))
    description = Column(Unicode(280))

    role = Column(SmallInteger, default=0)
    reputation = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<User:%s>' % self.username

    def __str__(self):
        return self.name or self.username

    def keys(self):
        return (
            'id', 'username', 'name', 'avatar_url', 'description',
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
        if not self._password:
            return False
        return check_password_hash(self._password, raw)

    @property
    def avatar_url(self):
        if not self._avatar_url:
            return None
        if self._avatar_url.startswith('http'):
            return self._avatar_url
        base = current_app.config['ZERQU_AVATAR_BASE']
        return '%s%s' % (base, self._avatar_url)

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


class UserSession(object):
    KEY_PREFIX = 'user_session:{}'

    def __init__(self, sid=None):
        if sid is None:
            sid = str(uuid.uuid4())

        self.sid = sid
        self._key = self.KEY_PREFIX.format(sid)

    @cached_property
    def value(self):
        return redis.hgetall(self._key)

    @cached_property
    def platform(self):
        return self.value.get('platform')

    @cached_property
    def browser(self):
        return self.value.get('browser')

    @cached_property
    def user_id(self):
        return self.value.get('user_id')

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)

    @property
    def last_used(self):
        return self.value.get('last_used')

    @last_used.setter
    def last_used(self, value):
        redis.hset(self._key, 'last_used', value)

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
        sess = cls()

        now = int(time.time())
        redis.hmset(sess._key, {
            'user_id': user.id,
            'platform': ua.platform,
            'browser': ua.browser,
            'created_at': now,
            'last_used': now,
        })
        session['id'] = sess.sid
        session['ts'] = now
        return sess

    @classmethod
    def logout(cls):
        sid = session.pop('id', None)
        if not sid:
            return False
        key = cls.KEY_PREFIX.format(sid)
        redis.delete(key)
        return True

    @classmethod
    def get_current_user(cls):
        """Get current authenticated user."""
        sid = session.get('id')
        if not sid:
            return None

        sess = cls(sid)

        if not sess.value or not sess.is_valid():
            session.pop('id', None)
            session.pop('ts', None)
            return None

        ts = session.get('ts')
        now = int(time.time())
        if ts and now - ts > 600:
            sess.last_used = now
            session['ts'] = now
        return sess.user
