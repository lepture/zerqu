# coding: utf-8

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
        rv = TopicLike.topic_like_counts([1, 2, 3])
        assert rv['1'] == 9

        rv = TopicLike.topic_like_counts([1, 2, 3])
        assert rv['2'] == 8
