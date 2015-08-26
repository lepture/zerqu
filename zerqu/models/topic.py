# coding: utf-8

import re
import datetime
from collections import defaultdict
from werkzeug.utils import cached_property
from sqlalchemy import func
from sqlalchemy import Column
from sqlalchemy import String, Unicode, DateTime
from sqlalchemy import SmallInteger, Integer, UnicodeText
from flask import current_app
from zerqu.libs.cache import cache, redis
from zerqu.libs.renderer import markup
from .user import User
from .webpage import WebPage
from .utils import current_user
from .base import db, Base, JSON, CACHE_TIMES

URL_PATTERN = re.compile(r'''^https?:\/\/[^\s<]+[^<.,:;"')\]\s]''')


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

    def __repr__(self):
        return '<Topic:%d>' % self.id

    def keys(self):
        return (
            'id', 'title', 'info', 'label', 'editable',
            'created_at', 'updated_at',
        )

    @property
    def editable(self):
        if not current_user:
            return False
        if current_user.id != self.user_id:
            return False
        valid_time = current_app.config.get('ZERQU_VALID_MODIFY_TIME')
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
        status = TopicStat(self.id) or {}
        rv = {
            'view_count': status.get('views', 0),
            'like_count': status.get('likes', 0),
            'comment_count': status.get('comments', 0),
            'read_count': status.get('reads', 0),
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
        stats = TopicStat.get_dict(tids)
        for tid in tids:
            status = stats.get(tid) or {}
            tid = str(tid)
            rv[tid] = {
                'view_count': status.get('views', 0),
                'like_count': status.get('likes', 0),
                'comment_count': status.get('comments', 0),
                'read_count': status.get('reads', 0),
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

    @classmethod
    def create_topic(cls, title, content, link, cafe_id, user_id):
        if not link:
            m = URL_PATTERN.match(content)
            if m:
                link = m.group(0)
                content = content[len(link):]

        topic = cls(
            title=title,
            content=content,
            cafe_id=cafe_id,
            user_id=user_id,
        )

        if not link:
            return topic

        webpage = WebPage.get_or_create(link, user_id)
        if webpage:
            topic.webpage = webpage.uuid
        return topic


class TopicStat(object):
    KEY_PREFIX = 'topic_stat:{}'

    def __init__(self, topic_id):
        self.topic_id = topic_id
        self.key = self.KEY_PREFIX.format(topic_id)

    def increase(self, field, step=1):
        redis.hincrby(self.key, field, step)

    def keys(self):
        return (
            'views', 'reads', 'flags', 'likes',
            'comments', 'reputation', 'timestamp',
        )

    def get(self, key, default=None):
        self.value.get(key, default)

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, item, value):
        redis.hset(self.key, item, int(value))

    @cached_property
    def value(self):
        return redis.hgetall(self.key)

    def calculate(self):
        def query_count(model):
            q = model.query.filter_by(topic_id=self.topic_id)
            return q.with_entities(func.count(1)).scalar()
        redis.hmset(self.key, dict(
            likes=query_count(TopicLike),
            reads=query_count(TopicRead),
            comments=query_count(Comment),
        ))

    @classmethod
    def get_many(cls, tids):
        with redis.pipeline() as pipe:
            for tid in tids:
                pipe.hgetall(cls.KEY_PREFIX.format(tid))
            return pipe.execute()

    @classmethod
    def get_dict(cls, tids):
        rv = cls.get_many(tids)
        return dict(zip(tids, rv))


class TopicLike(Base):
    __tablename__ = 'zq_topic_like'

    topic_id = Column(Integer, primary_key=True, autoincrement=False)
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, topic_id, user_id):
        self.topic_id =topic_id
        self.user_id = user_id

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
