# coding: utf-8

from flask import json
from zerqu.models import db, TopicLike
from ._base import TestCase


class TestTopicLikes(TestCase):
    def test_topic_likes(self):
        for i in range(1, 10):
            db.session.add(TopicLike(topic_id=1, user_id=i))

        for i in range(1, 9):
            db.session.add(TopicLike(topic_id=2, user_id=i))

        for i in range(2, 12):
            db.session.add(TopicLike(topic_id=3, user_id=i))

        db.session.commit()
        rv = TopicLike.topics_like_counts([1, 2, 3])
        assert rv['1'] == 9

        rv = TopicLike.topics_like_counts([1, 2, 3])
        assert rv['2'] == 8

    def test_topics_liked_by_user(self):
        db.session.add(TopicLike(topic_id=1, user_id=1))
        db.session.add(TopicLike(topic_id=2, user_id=1))
        db.session.commit()

        rv = TopicLike.topics_liked_by_user(user_id=1, topic_ids=[1, 2, 3])
        assert rv['1'] is not None
        assert rv['2'] is not None
        assert rv['3'] is None

        # read from cache
        rv = TopicLike.topics_liked_by_user(user_id=1, topic_ids=[1, 2])
        assert rv['1'] is not None
        assert rv['2'] is not None


class TestTopicsStatuses(TestCase):
    def test_invalid_request(self):
        rv = self.client.get('/api/topics/statuses')
        assert rv.status_code == 400
        rv = self.client.get('/api/topics/statuses?topics=sb')
        assert rv.status_code == 400

    def test_get_statuses(self):
        for i in range(1, 10):
            db.session.add(TopicLike(topic_id=1, user_id=i))
        for i in range(1, 9):
            db.session.add(TopicLike(topic_id=2, user_id=i))
        db.session.commit()
        rv = self.client.get('/api/topics/statuses?topics=1,2')
        data = json.loads(rv.data)
        assert data['1']['like_count'] == 9
        assert data['2']['like_count'] == 8

    def test_liked_statuses(self):
        db.session.add(TopicLike(topic_id=1, user_id=2))
        db.session.add(TopicLike(topic_id=2, user_id=1))
        headers = self.get_authorized_header(user_id=2)
        rv = self.client.get(
            '/api/topics/statuses?topics=1,2',
            headers=headers
        )
        data = json.loads(rv.data)
        assert 'liked_by_me' in data['1']
        assert 'liked_by_me' not in data['2']
