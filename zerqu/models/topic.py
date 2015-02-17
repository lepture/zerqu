# coding: utf-8

import datetime
from werkzeug.utils import cached_property
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer, Text
from .user import User
from .base import Base, JSON


class Topic(Base):
    __tablename__ = 'zq_topic'

    id = Column(Integer, primary_key=True)
    title = Column(String(140), nullable=False)
    content = Column(Text, default='')

    # feature content
    feature = Column(JSON, default={})

    cafe_id = Column(Integer)
    user_id = Column(Integer, nullable=False)

    status = Column(SmallInteger, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def keys(self):
        return (
            'id', 'title', 'content', 'feature',
            'user_id', 'created_at', 'updated_at',
        )

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)


class Comment(Base):
    __tablename__ = 'zq_comment'

    id = Column(Integer, primary_key=True)
    content = Column(String(480), nullable=False)

    topic_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)

    status = Column(SmallInteger, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def keys(self):
        return (
            'id', 'topic_id', 'user_id', 'content',
            'created_at', 'updated_at',
        )
