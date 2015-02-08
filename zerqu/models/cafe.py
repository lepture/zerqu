# coding: utf-8

import datetime
from werkzeug.utils import cached_property
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer
from .user import User
from .base import Base

__all__ = ['Cafe']


class Cafe(Base):
    __tablename__ = 'zq_cafe'

    STATUS = {
        0: 'closed',
        1: 'active',
        2: 'verified',
        9: 'official',
    }

    PERMISSION = {
        0: 'public',
        1: 'subscriber',
        2: 'member',
        9: 'private',
    }

    id = Column(Integer, primary_key=True)

    # basic information
    slug = Column(String(24), unique=True)
    name = Column(String(30), unique=True)
    description = Column(String(280))

    # front style
    logo_url = Column(String(260))
    base_color = Column(40)
    text_color = Column(40)
    background_color = Column(40)
    background_url = Column(String(260))

    # available feature
    _feature = Column('feature', SmallInteger, default=0)
    _permission = Column('permission', default=0)

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
            'id', 'slug', 'name', 'logo_url', 'description',
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

    STATUS = {
        0: 'visitor',
        1: 'subscriber',
        2: 'member',
        9: 'admin',
    }

    cafe_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    status = Column(SmallInteger, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
