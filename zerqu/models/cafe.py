# coding: utf-8

import datetime
from flask import current_app
from werkzeug.utils import cached_property
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer
from .user import User
from .base import db, Base, JSON
from ..libs.utils import EMPTY

__all__ = ['Cafe', 'CafeMember']


class Cafe(Base):
    __tablename__ = 'zq_cafe'

    STATUSES = {
        0: 'closed',
        1: 'active',
        6: 'verified',
        9: 'official',
    }
    STATUS_VERIFIED = 6
    STATUS_OFFICIAL = 9

    # everyone can read and write
    PERMISSION_PUBLIC = 0
    # everyone can read, only subscriber can write
    PERMISSION_SUBSCRIBER = 3
    # everyone can read, only member can write
    PERMISSION_MEMBER = 6
    # only member can read and write
    PERMISSION_PRIVATE = 9

    PERMISSIONS = {
        'public': PERMISSION_PUBLIC,
        'subscriber': PERMISSION_SUBSCRIBER,
        'member': PERMISSION_MEMBER,
        'private': PERMISSION_PRIVATE,
    }

    id = Column(Integer, primary_key=True)

    # basic information
    slug = Column(String(30), nullable=False, unique=True, index=True)
    name = Column(String(30), nullable=False, unique=True)
    description = Column(String(140))
    # refer to a topic ID as introduction
    intro = Column(Integer)

    style = Column(JSON, default={
        'logo': None,
        'color': None,
        'cover': None,
    })

    # available features
    _features = Column('features', Integer, default=0)

    # defined above
    permission = Column(SmallInteger, default=0)

    # meta data
    status = Column(SmallInteger, default=1)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    __reference__ = {'user': 'user_id'}

    def __repr__(self):
        return '<Cafe:%s>' % self.slug

    def __str__(self):
        return self.name

    def keys(self):
        return (
            'id', 'slug', 'name', 'style', 'description', 'intro',
            'features', 'label', 'is_active', 'created_at', 'updated_at',
        )

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)

    @cached_property
    def is_active(self):
        return self.status > 0

    @cached_property
    def label(self):
        label = self.STATUSES.get(self.status)
        if label == 'active':
            return None
        return label

    @cached_property
    def features(self):
        if not self._features:
            return []

        rv = []
        defines = current_app.config.get('ZERQU_FEATURE_DEFINES')
        for k in defines:
            if defines[k] & self._features:
                rv.append(k)
        return rv

    def has_read_permission(self, user_id, membership=EMPTY):
        if self.permission != self.PERMISSION_PRIVATE:
            return True

        if not user_id:
            return False

        if self.user_id == user_id:
            return True

        if membership is EMPTY:
            membership = CafeMember.cache.get((self.id, user_id))

        if not membership:
            return False

        role = membership.role
        return role in (CafeMember.ROLE_MEMBER, CafeMember.ROLE_ADMIN)

    def has_write_permission(self, user_id, membership=EMPTY):
        if not user_id:
            return False

        if self.permission == self.PERMISSION_PUBLIC:
            return True

        if self.user_id == user_id:
            return True

        if membership is EMPTY:
            membership = CafeMember.cache.get((self.id, user_id))

        if not membership:
            return False

        role = membership.role
        limited = (self.PERMISSION_PRIVATE, self.PERMISSION_MEMBER)
        if self.permission in limited:
            return role in (CafeMember.ROLE_MEMBER, CafeMember.ROLE_ADMIN)

        return role != CafeMember.ROLE_VISITOR

    def has_admin_permission(self, user_id, membership=EMPTY):
        if not user_id:
            return False

        if self.user_id == user_id:
            return True

        if membership is EMPTY:
            membership = CafeMember.cache.get((self.id, user_id))

        if not membership:
            return False

        return membership.role == CafeMember.ROLE_ADMIN


class CafeMember(Base):
    __tablename__ = 'zq_cafe_member'

    # not joined, but has topics or comments in this cafe
    ROLE_VISITOR = 0
    # asking for joining a private cafe
    ROLE_APPLICANT = 1
    # subscribed a cafe
    ROLE_SUBSCRIBER = 2
    # authorized member of a private cafe
    ROLE_MEMBER = 3
    # people who can change cafe descriptions
    ROLE_ADMIN = 9

    ROLE_LABELS = {
        ROLE_VISITOR: 'visitor',
        ROLE_APPLICANT: 'applicant',
        ROLE_SUBSCRIBER: 'subscriber',
        ROLE_MEMBER: 'member',
        ROLE_ADMIN: 'admin',
    }

    cafe_id = Column(Integer, primary_key=True, autoincrement=False)
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    role = Column('role', SmallInteger, default=0)

    reputation = Column(Integer, default=0)
    description = Column(String(140))

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    @cached_property
    def label(self):
        return self.ROLE_LABELS.get(self.role)

    def keys(self):
        return [
            'cafe_id', 'user_id', 'reputation', 'description',
            'label', 'created_at', 'updated_at',
        ]

    @classmethod
    def get_or_create(cls, cafe_id, user_id):
        m = cls.cache.get((cafe_id, user_id))
        if m:
            return m
        m = cls(cafe_id=cafe_id, user_id=user_id)
        db.session.add(m)
        return m

    @classmethod
    def get_user_following_cafe_ids(cls, user_id):
        # TODO: cache
        q = db.session.query(cls.cafe_id).filter_by(user_id=user_id)
        q = q.filter(cls.role >= cls.ROLE_SUBSCRIBER)
        return {cafe_id for cafe_id, in q}

    @classmethod
    def get_user_following_public_cafe_ids(cls, user_id):
        q = db.session.query(cls.cafe_id).filter_by(user_id=user_id)
        q = q.filter(cls.role >= cls.ROLE_SUBSCRIBER)
        q = q.join(Cafe, Cafe.id == cls.cafe_id)
        q = q.filter(Cafe.permission != Cafe.PERMISSION_PRIVATE)
        return {cafe_id for cafe_id, in q}

    @classmethod
    def get_cafe_admin_ids(cls, cafe_id):
        q = db.session.query(cls.user_id).filter_by(cafe_id=cafe_id)
        q = q.filter_by(role=cls.ROLE_ADMIN)
        return {user_id for user_id, in q}
