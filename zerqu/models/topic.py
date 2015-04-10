# coding: utf-8

import datetime
from werkzeug.utils import cached_property
from sqlalchemy import Column
from sqlalchemy import String, DateTime
from sqlalchemy import SmallInteger, Integer, Text
from .user import User
from .base import cache, Base, JSON, CACHE_TIMES


class Topic(Base):
    __tablename__ = 'zq_topic'

    STATUSES = {
        0: 'closed',
        3: 'featured',
        6: 'promoted',
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

    __reference__ = {'user': 'user_id', 'cafe': 'cafe_id'}

    def keys(self):
        return (
            'id', 'title', 'link', 'info', 'label',
            'created_at', 'updated_at',
        )

    @property
    def label(self):
        return self.STATUSES.get(self.status)

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)


class TopicLike(Base):
    __tablename__ = 'zq_topic_like'

    topic_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def topics_like_counts(cls, topic_ids):
        return topic_ref_counts(cls, topic_ids)

    @classmethod
    def topics_liked_by_user(cls, user_id, topic_ids):
        return topic_ref_current_user(cls, user_id, topic_ids)


class TopicRead(Base):
    __tablename__ = 'zq_topic_read'

    topic_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # reading status
    _percent = Column('percent', SmallInteger, default=0)

    @property
    def percent(self):
        return '%d%%' % self._percent

    @percent.setter
    def percent(self, num):
        if 0 < num <= 100:
            self._percent = num

    @classmethod
    def topics_read_counts(cls, topic_ids):
        return topic_ref_counts(cls, topic_ids)

    @classmethod
    def topics_read_by_user(cls, user_id, topic_ids):
        return topic_ref_current_user(cls, user_id, topic_ids)


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
    def topics_comment_counts(cls, topic_ids):
        return topic_ref_counts(cls, topic_ids)


class CommentLike(Base):
    __tablename__ = 'zq_comment_like'

    comment_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
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


def topic_ref_current_user(cls, user_id, topic_ids):
    prefix = cls.generate_cache_prefix('get')

    def gen_key(tid):
        return prefix + '-'.join(map(str, [tid, user_id]))

    def get_key(key):
        return key.lstrip(prefix).split('-')[0]

    rv = cache.get_dict(*[gen_key(tid) for tid in topic_ids])
    missed = {i for i in topic_ids if rv[gen_key(i)] is None}
    rv = {get_key(k): rv[k] for k in rv}
    if not missed:
        return rv

    to_cache = {}
    q = cls.cache.filter_by(user_id=user_id)
    for item in q.filter(cls.topic_id.in_(missed)):
        rv[str(item.topic_id)] = item
        to_cache[gen_key(item.topic_id)] = item

    cache.set_many(to_cache, CACHE_TIMES['get'])
    return rv
