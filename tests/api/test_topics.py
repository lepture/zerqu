# coding: utf-8

from flask import json
from zerqu.models import db, User, Topic, TopicLike
from zerqu.models import Cafe, Comment
from ._base import TestCase


class TopicMixin(object):
    def create_public_topic(self):
        cafe = Cafe(
            name=u'pub', slug='pub', user_id=1,
            permission=Cafe.PERMISSION_PUBLIC, status=9,
        )
        db.session.add(cafe)
        db.session.flush()
        topic = Topic(title=u'hello', user_id=1, cafe_id=cafe.id)
        db.session.add(topic)
        db.session.commit()
        return topic


class TestTopicTimeline(TestCase):
    def create_topics(self):
        pub_cafe = Cafe(
            name=u'official', slug='official', user_id=1,
            permission=Cafe.PERMISSION_PUBLIC, status=9,
        )
        member_cafe = Cafe(
            name=u'private', slug='private', user_id=1,
            permission=Cafe.PERMISSION_MEMBER, status=1,
        )
        db.session.add(pub_cafe)
        db.session.add(member_cafe)
        db.session.flush()

        for i in range(30):
            t1 = Topic(user_id=1, cafe_id=pub_cafe.id, title=u'hi public')
            t2 = Topic(user_id=2, cafe_id=member_cafe.id, title=u'hi member')
            db.session.add(t1)
            db.session.add(t2)
        db.session.commit()

    def test_public_timeline(self):
        self.create_topics()
        rv = self.client.get('/api/topics/timeline')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert len(set([d['cafe']['id'] for d in data['data']])) == 1

    def test_show_all_timeline(self):
        self.create_topics()
        rv = self.client.get('/api/topics/timeline?show=all')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert len(set([d['cafe']['id'] for d in data['data']])) == 2


class TestViewTopic(TestCase):
    def create_topic(self, cafe=None):
        if cafe is None:
            cafe = Cafe(name=u'official', slug='official', user_id=1)
            db.session.add(cafe)
            db.session.commit()

        t = Topic(
            user_id=1,
            cafe_id=cafe.id,
            title=u'View',
            content=u'A **text**',
        )
        db.session.add(t)
        db.session.commit()
        return t

    def test_markup_content(self):
        t = self.create_topic()
        rv = self.client.get('/api/topics/%d' % t.id)
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert '<strong>' in data['content']

    def test_raw_content(self):
        t = self.create_topic()
        rv = self.client.get('/api/topics/%d?content=raw' % t.id)
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert '<strong>' not in data['content']

    def test_view_topic_with_login(self):
        t = self.create_topic()
        headers = self.get_authorized_header(user_id=1)
        rv = self.client.get('/api/topics/%d' % t.id, headers=headers)
        data = json.loads(rv.data)
        assert data['editable']


class TestUpdateTopic(TestCase, TopicMixin):
    def test_not_found(self):
        headers = self.get_authorized_header(user_id=1, scope='topic:write')
        rv = self.client.post('/api/topics/404', headers=headers)
        assert rv.status_code == 404

    def test_permission_denied(self):
        t = self.create_public_topic()
        headers = self.get_authorized_header(
            user_id=t.user_id + 1,
            scope='topic:write',
        )
        rv = self.client.post('/api/topics/%d' % t.id, headers=headers)
        assert rv.status_code == 403

    def test_update_success(self):
        t = self.create_public_topic()
        headers = self.get_authorized_header(
            user_id=t.user_id,
            scope='topic:write',
        )
        rv = self.client.post(
            '/api/topics/%d' % t.id,
            data=json.dumps({'title': 'Changed', 'content': '**strong**'}),
            headers=headers,
        )
        assert rv.status_code == 200
        assert t.title == u'Changed'


class TestTopicLikes(TestCase, TopicMixin):
    def test_topic_likes(self):
        for i in range(1, 10):
            db.session.add(TopicLike(topic_id=1, user_id=i))

        for i in range(1, 9):
            db.session.add(TopicLike(topic_id=2, user_id=i))

        for i in range(2, 12):
            db.session.add(TopicLike(topic_id=3, user_id=i))

        db.session.commit()

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

    def test_request_like_topic(self):
        topic = self.create_public_topic()
        headers = self.get_authorized_header(user_id=2)
        url = '/api/topics/%d/likes' % topic.id
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 409

        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 204
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 409

    def test_view_topic_likes(self):
        topic = Topic(title=u'hello', user_id=1)
        db.session.add(topic)
        db.session.commit()
        for i in range(10, 100):
            db.session.add(TopicLike(user_id=i, topic_id=topic.id))
            name = 'foo-%d' % i
            user = User(id=i, username=name, email='%s@gmail.com' % name)
            db.session.add(user)
        db.session.commit()

        url = '/api/topics/%d/likes' % topic.id
        rv = self.client.get(url)
        data = json.loads(rv.data)
        assert data['pagination']['total'] == 90

        db.session.add(TopicLike(user_id=1, topic_id=topic.id))
        db.session.commit()
        headers = self.get_authorized_header(user_id=2)
        rv = self.client.get(url, headers=headers)
        data = json.loads(rv.data)
        assert data['data'][0]['id'] != 1

        headers = self.get_authorized_header(user_id=1)
        rv = self.client.get(url, headers=headers)
        data = json.loads(rv.data)
        assert data['data'][0]['id'] == 1

        headers = self.get_authorized_header(user_id=12)
        rv = self.client.get(url, headers=headers)
        data = json.loads(rv.data)
        assert data['data'][0]['id'] == 12


class TestTopicFlag(TestCase, TopicMixin):
    def test_flag_topic(self):
        headers = self.get_authorized_header()
        t = self.create_public_topic()
        url = '/api/topics/%d/flag' % t.id
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204

        url = '/api/topics/%d/flag' % t.id
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204


class TestTopicRead(TestCase, TopicMixin):
    def test_record_read_percent(self):
        topic = self.create_public_topic()
        headers = self.get_authorized_header(user_id=2)
        url = '/api/topics/%d/read' % topic.id

        rv = self.client.post(
            url, data=json.dumps({'percent': 's'}), headers=headers
        )
        assert rv.status_code == 400

        rv = self.client.post(
            url, data=json.dumps({'percent': 100}), headers=headers
        )
        assert b'percent' in rv.data

        rv = self.client.post(
            url, data=json.dumps({'percent': 200}), headers=headers
        )
        assert b'100%' in rv.data


class TestTopicComment(TestCase, TopicMixin):
    def create_topic_comments(self, topic_id):
        for i in range(30):
            c = Comment(user_id=1, topic_id=topic_id, content=u'haha %d' % i)
            db.session.add(c)
        db.session.commit()

    def test_create_topic_comment(self):
        topic = self.create_public_topic()
        headers = self.get_authorized_header(user_id=2, scope='comment:write')
        url = '/api/topics/%d/comments' % topic.id
        rv = self.client.post(
            url, data=json.dumps({'content': '**s**'}),
            headers=headers
        )
        assert rv.status_code == 201
        assert b'<strong>' in rv.data

    def test_view_topic_comments(self):
        topic = self.create_public_topic()
        self.create_topic_comments(topic.id)
        url = '/api/topics/%d/comments' % topic.id
        rv = self.client.get(url)
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['cursor']

    def test_delete_topic_comment_not_found(self):
        topic = self.create_public_topic()
        url = '/api/topics/%d/comments/404' % topic.id
        headers = self.get_authorized_header(user_id=1, scope='comment:write')
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 404

        self.create_topic_comments(topic.id + 1)
        c = Comment.query.filter_by(topic_id=topic.id + 1).first()
        url = '/api/topics/%d/comments/%d' % (topic.id, c.id)
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 404

    def test_delete_topic_comment_denied(self):
        topic = self.create_public_topic()
        self.create_topic_comments(topic.id)
        c = Comment.query.filter_by(topic_id=topic.id).first()
        url = '/api/topics/%d/comments/%d' % (topic.id, c.id)
        headers = self.get_authorized_header(user_id=2, scope='comment:write')
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 403

    def test_delete_topic_comment_success(self):
        topic = self.create_public_topic()
        self.create_topic_comments(topic.id)
        c = Comment.query.filter_by(topic_id=topic.id).first()
        url = '/api/topics/%d/comments/%d' % (topic.id, c.id)
        headers = self.get_authorized_header(user_id=1, scope='comment:write')
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 204

    def test_flag_topic_comment(self):
        topic = self.create_public_topic()
        self.create_topic_comments(topic.id)
        c = Comment.query.filter_by(topic_id=topic.id).first()
        url = '/api/topics/%d/comments/%d/flag' % (topic.id, c.id)
        headers = self.get_authorized_header(user_id=1, scope='comment:write')
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204
        assert c.flag_count == 1

        # keep the same
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204
        assert c.flag_count == 1
