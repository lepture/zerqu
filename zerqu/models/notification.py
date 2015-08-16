# coding: utf-8

import re
import datetime
from flask import json
from sqlalchemy import event
from zerqu.libs.cache import redis
from zerqu.libs.utils import Pagination, run_task
from .topic import Topic, TopicLike, Comment, CommentLike
from .user import User


class Notification(object):
    CATEGORY_COMMENT = 'comment'
    CATEGORY_MENTION = 'mention'
    CATEGORY_REPLY = 'reply'
    CATEGORY_LIKE_TOPIC = 'like_topic'
    CATEGORY_LIKE_COMMENT = 'like_comment'

    def __init__(self, user_id):
        self.user_id = user_id
        self.key = 'notification_list:{}'.format(user_id)

    def add(self, sender_id, category, topic_id, **kwargs):
        kwargs['sender_id'] = sender_id
        kwargs['topic_id'] = topic_id
        kwargs['category'] = category
        kwargs['created_at'] = datetime.datetime.utcnow()
        redis.lpush(self.key, json.dumps(kwargs))

    def count(self):
        return redis.llen(self.key)

    def get(self, index):
        rv = redis.lrange(self.key, index, index)
        if rv:
            return rv[0]
        return None

    def flush(self):
        redis.delete(self.key)

    def paginate(self, page=1, perpage=20):
        total = self.count()
        p = Pagination(total, page=page, perpage=perpage)
        start = (p.page - 1) * p.perpage
        stop = start + p.perpage
        return redis.lrange(self.key, start, stop), p

    @staticmethod
    def process_notifications(items):
        topic_ids = set()
        user_ids = set()
        data = []
        for d in items:
            d = json.loads(d)
            user_ids.add(d['sender_id'])
            topic_ids.add(d['topic_id'])
            data.append(d)

        topics = Topic.cache.get_dict(topic_ids)
        users = User.cache.get_dict(user_ids)

        for d in data:
            d['sender'] = users.get(str(d.pop('sender_id')))
            d['topic'] = topics.get(str(d.pop('topic_id')))
        return data


def add_notification_event_listener():

    @event.listens_for(Comment, 'after_insert')
    def record_comment(mapper, conn, target):
        run_task(_record_comment, target)

    @event.listens_for(TopicLike, 'after_insert')
    def record_like_topic(mapper, conn, target):
        run_task(_record_like_topic, target)

    @event.listens_for(CommentLike, 'after_insert')
    def record_like_comment(mapper, conn, target):
        run_task(_record_like_comment, target)


def _record_comment(comment):
    topic = Topic.cache.get(comment.topic_id)
    if not topic:
        return
    if topic.user_id != comment.user_id:
        Notification(topic.user_id).add(
            comment.user_id,
            Notification.CATEGORY_COMMENT,
            comment.topic_id,
            comment_id=comment.id,
        )

    names = re.findall(r'(?:^|\s)@([0-9a-z]+)', comment.content)
    for username in names:
        user = User.cache.filter_first(username=username)
        if user.id == comment.user_id:
            continue

        Notification(user.id).add(
            comment.user_id,
            Notification.CATEGORY_MENTION,
            comment.topic_id,
            comment_id=comment.id,
        )


def _record_like_topic(like):
    topic = Topic.cache.get(like.topic_id)
    if not topic:
        return
    if topic.user_id != like.user_id:
        Notification(topic.user_id).add(
            like.user_id,
            Notification.CATEGORY_LIKE_TOPIC,
            like.topic_id,
        )


def _record_like_comment(like):
    comment = Comment.cache.get(like.comment_id)
    if not comment:
        return
    if comment.user_id != like.user_id:
        Notification(comment.user_id).add(
            like.user_id,
            Notification.CATEGORY_LIKE_COMMENT,
            comment.topic_id,
            comment_id=like.comment_id,
        )
