# coding: utf-8

import datetime
from flask import json
from zerqu.libs.cache import redis
from zerqu.libs.utils import Pagination
from .topic import Topic
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
