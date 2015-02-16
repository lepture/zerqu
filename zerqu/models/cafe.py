# coding: utf-8

import datetime
from werkzeug.utils import cached_property
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer
from .user import User
from .base import Base, JSON

__all__ = ['Cafe', 'CafeMember']


class Cafe(Base):
    __tablename__ = 'zq_cafe'

    STATUS = {
        0: 'closed',
        1: 'active',
        6: 'verified',
        9: 'official',
    }

    # everyone can read and write
    PERMISSION_PUBLIC = 0
    # everyone can read, only subscriber can write
    PERMISSION_SUBSCRIBER = 3
    # everyone can read, only member can write
    PERMISSION_MEMBER = 6
    # only member can read and write
    PERMISSION_PRIVATE = 9

    id = Column(Integer, primary_key=True)

    # basic information
    slug = Column(String(24), nullable=False, unique=True)
    name = Column(String(30), nullable=False, unique=True)
    description = Column(String(280))

    # logo_url, base_color, text_color, background_color, background_url
    style = Column(JSON, default={
        'logo_url': None,
        'base_color': None,
        'text_color': None,
        'background_color': None,
        'background_url': None,
    })

    # available feature
    feature = Column(String(10), default='text')
    # defined above
    permission = Column(SmallInteger, default=0)

    # meta data
    status = Column(SmallInteger, default=1)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<Cafe:%s>' % self.slug

    def __str__(self):
        return self.name

    def keys(self):
        return (
            'id', 'slug', 'name', 'style', 'description',
            'label', 'user_id', 'is_active', 'created_at', 'updated_at',
        )

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)

    @cached_property
    def is_active(self):
        return self.status > 0

    @cached_property
    def label(self):
        label = self.STATUS.get(self.status)
        if label == 'active':
            return None
        return label


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

    cafe_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    role = Column('role', SmallInteger, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    @cached_property
    def label(self):
        if self.role == self.ROLE_VISITOR:
            return 'visitor'
        if self.role == self.ROLE_APPLICANT:
            return 'applicant'
        if self.role == self.ROLE_SUBSCRIBER:
            return 'subscriber'
        if self.role == self.ROLE_MEMBER:
            return 'member'
        if self.role == self.ROLE_ADMIN:
            return 'admin'
        return None

    def keys(self):
        return ['cafe_id', 'user_id', 'label', 'created_at', 'updated_at']
