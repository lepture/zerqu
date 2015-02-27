# coding: utf-8

import datetime
from werkzeug.utils import cached_property
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer, Text, Boolean
from .user import User
from .base import cache, Base, JSON


class Topic(Base):
    __tablename__ = 'zq_topic'

    STATUS = {
        0: 'close',
        1: 'open',
        9: 'feature',
    }

    id = Column(Integer, primary_key=True)
    title = Column(String(140), nullable=False)
    link = Column(String(260))
    content = Column(Text, default='')

    # feature content
    info = Column(JSON, default={})

    cafe_id = Column(Integer)
    user_id = Column(Integer, nullable=False)

    status = Column(SmallInteger, default=1)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def keys(self):
        return (
            'id', 'title', 'link', 'content', 'info', 'label',
            'cafe_id', 'user_id', 'created_at', 'updated_at',
        )

    @property
    def label(self):
        return self.STATUS.get(self.status)

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)


class TopicLike(Base):
    __tablename__ = 'zq_topic_like'

    topic_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def topic_like_counts(cls, topic_ids):
        return topic_ref_counts(cls, topic_ids)


class TopicVote(Base):
    __tablename__ = 'zq_topic_vote'

    topic_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    upvote = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


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

    @classmethod
    def topic_comment_counts(cls, topic_ids):
        return topic_ref_counts(cls, topic_ids)


class CommentVote(Base):
    __tablename__ = 'zq_comment_vote'

    comment_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    upvote = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def topic_ref_counts(cls, topic_ids):
    prefix = cls.generate_cache_prefix('fc') + 'topic_id$'
    rv = cache.get_dict(*[prefix + str(i) for i in topic_ids])

    missed = {i for i in topic_ids if rv[prefix + str(i)] is None}
    rv = {k.lstrip(prefix): rv[k] for k in rv}

    if not missed:
        return rv

    for tid in missed:
        rv[str(tid)] = cls.cache.filter_count(topic_id=tid)

    return rv
