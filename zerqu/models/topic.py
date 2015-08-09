# coding: utf-8

import datetime
from collections import defaultdict
from werkzeug.utils import cached_property
from sqlalchemy import func
from sqlalchemy import Column
from sqlalchemy import String, Unicode, DateTime
from sqlalchemy import SmallInteger, Integer, UnicodeText
from .user import User
from .base import db, Base, JSON, CACHE_TIMES
from ..libs.cache import cache
from ..libs.renderer import markup


class Topic(Base):
    __tablename__ = 'zq_topic'

    STATUSES = {
        0: 'closed',
        3: 'featured',
        6: 'promoted',
    }

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(140), nullable=False)
    webpage = Column(String(34))
    content = Column(UnicodeText, default=u'')

    # feature content
    info = Column(JSON, default={})

    cafe_id = Column(Integer, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    # A topic copied from another topic
    fork_id = Column(Integer)

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
            'id', 'title', 'info', 'label',
            'created_at', 'updated_at',
        )

    def is_changeable(self, valid_time):
        if not valid_time:
            return True
        delta = datetime.datetime.utcnow() - self.created_at
        return delta.total_seconds() < valid_time

    @property
    def label(self):
        return self.STATUSES.get(self.status)

    def get_html_content(self):
        return markup(self.content)

    @cached_property
    def user(self):
        return User.cache.get(self.user_id)

    def get_statuses(self, user_id=None):
        status = TopicStatus.cache.get(self.id)
        rv = {
            'view_count': status.views,
            'like_count': status.likes,
            'read_count': status.reads,
            'comment_count': status.comments,
        }
        if not user_id:
            return rv

        key = (self.id, user_id)
        rv['liked_by_me'] = bool(TopicLike.cache.get(key))
        read = TopicRead.cache.get(key)
        if read:
            rv['read_by_me'] = read.percent
        else:
            rv['read_by_me'] = '0%'
            read = TopicRead(topic_id=self.id, user_id=user_id)
            with db.auto_commit(throw=False):
                db.session.add(read)
        return rv

    @staticmethod
    def get_multi_statuses(tids, user_id):
        rv = {}

        statuses = TopicStatus.cache.get_dict(tids)

        for tid in tids:
            tid = str(tid)
            status = statuses.get(tid)
            if status:
                rv[tid] = {
                    'view_count': status.views,
                    'like_count': status.likes,
                    'comment_count': status.comments,
                    'read_count': status.reads,
                }
            else:
                rv[tid] = {
                    'view_count': 0,
                    'like_count': 0,
                    'comment_count': 0,
                    'read_count': 0,
                }

        if not user_id:
            return rv

        liked = TopicLike.topics_liked_by_user(user_id, tids)
        reads = TopicRead.topics_read_by_user(user_id, tids)
        for tid in tids:
            tid = str(tid)
            rv[tid]['liked_by_me'] = bool(liked.get(tid))
            item = reads.get(tid)
            if item:
                rv[tid]['read_by_me'] = item.percent
        return rv


class TopicStatus(Base):
    __tablename__ = 'zq_topic_status'

    topic_id = Column(Integer, primary_key=True, autoincrement=False)
    views = Column(Integer, default=1)
    reads = Column(Integer, default=0)
    flags = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    timestamp = Column(Integer, default=0)
    reputation = Column(Integer, default=0)

    def keys(self):
        return (
            'views', 'reads', 'flags', 'likes',
            'comments', 'reputation',
        )

    @classmethod
    def get_or_create(cls, topic_id):
        data = cls.query.get(topic_id)
        if not data:
            data = cls(topic_id=topic_id)
            db.session.add(data)
            db.session.flush()
        return data

    @classmethod
    def increase(cls, topic_id, key):
        # TODO: use redis
        status = cls.get_or_create(topic_id)
        count = getattr(status, key, 0)
        setattr(status, key, count + 1)
        with db.auto_commit(False):
            db.session.add(status)

    def calculate(self):

        def query_count(model):
            q = model.query.filter_by(topic_id=self.topic_id)
            return q.with_entities(func.count(1)).scalar()

        self.likes = query_count(TopicLike)
        self.reads = query_count(TopicRead)
        self.comments = query_count(Comment)
        db.session.add(self)


class TopicLike(Base):
    __tablename__ = 'zq_topic_like'

    topic_id = Column(Integer, primary_key=True, autoincrement=False)
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def topics_liked_by_user(cls, user_id, topic_ids):
        return fetch_current_user_items(cls, user_id, topic_ids)


class TopicRead(Base):
    __tablename__ = 'zq_topic_read'

    topic_id = Column(Integer, primary_key=True, autoincrement=False)
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # reading status
    _percent = Column('percent', SmallInteger, default=0)

    @property
    def percent(self):
        return '%d%%' % self._percent

    @percent.setter
    def percent(self, num):
        if self._percent == 100:
            # finished already
            return
        if 0 < num <= 100:
            self._percent = num

    @classmethod
    def topics_read_by_user(cls, user_id, topic_ids):
        return fetch_current_user_items(cls, user_id, topic_ids)


class Comment(Base):
    __tablename__ = 'zq_comment'

    id = Column(Integer, primary_key=True)
    content = Column(UnicodeText, nullable=False)

    topic_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    # comment reply to another comment
    reply_to = Column(Integer)

    status = Column(SmallInteger, default=0)
    flag_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    __reference__ = {'user': 'user_id'}

    def keys(self):
        return (
            'id', 'topic_id', 'user_id', 'content', 'reply_to',
            'created_at', 'updated_at', 'flag_count', 'like_count',
        )

    def reset_like_count(self):
        q = CommentLike.query.filter_by(comment_id=self.id)
        self.like_count = q.with_entities(func.count(1)).scalar()
        db.session.add(self)
        return self.like_count

    @staticmethod
    def get_multi_statuses(comment_ids, user_id):
        liked = CommentLike.comments_liked_by_user(user_id, comment_ids)
        rv = defaultdict(dict)
        for cid in comment_ids:
            cid = str(cid)
            item = liked.get(cid)
            rv[cid]['liked_by_me'] = bool(item)
        return rv


class CommentLike(Base):
    __tablename__ = 'zq_comment_like'

    comment_id = Column(Integer, primary_key=True, autoincrement=False)
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def comments_liked_by_user(cls, user_id, comment_ids):
        return fetch_current_user_items(
            cls, user_id, comment_ids, key='comment_id'
        )


def fetch_current_user_items(cls, user_id, ref_ids, key='topic_id'):
    if not ref_ids:
        return {}

    prefix = cls.generate_cache_prefix('get')

    def gen_key(tid):
        return prefix + '-'.join(map(str, [tid, user_id]))

    def get_key(key):
        return key.lstrip(prefix).split('-')[0]

    rv = cache.get_dict(*[gen_key(tid) for tid in ref_ids])
    missed = {i for i in ref_ids if rv[gen_key(i)] is None}
    rv = {get_key(k): rv[k] for k in rv}
    if not missed:
        return rv

    to_cache = {}
    q = cls.cache.filter_by(user_id=user_id)
    for item in q.filter(getattr(cls, key).in_(missed)):
        rv[str(getattr(item, key))] = item
        to_cache[gen_key(getattr(item, key))] = item

    cache.set_many(to_cache, CACHE_TIMES['get'])
    return rv


def topic_list_with_statuses(topics, user_id):
    """Update topic list with statuses.

    :param topics: A list of topic dict.
    :param user_id: Current user ID.
    """
    rv = []
    statuses = Topic.get_multi_statuses([t['id'] for t in topics], user_id)
    for t in topics:
        t.update(statuses.get(str(t['id']), {}))
        rv.append(t)
    return rv
