# coding: utf-8

import random
from flask import json
from zerqu.models import db, User, Cafe, CafeMember, Topic
from ._base import TestCase


class CafeMixin(object):
    def create_cafes(self, num=30):
        for i in range(num):
            permission = random.choice([
                Cafe.PERMISSION_PUBLIC,
                Cafe.PERMISSION_SUBSCRIBER,
                Cafe.PERMISSION_MEMBER,
                Cafe.PERMISSION_PRIVATE,
            ])
            status = random.choice(list(Cafe.STATUSES.keys()))
            name = '%s-%d' % (random.choice(['foo', 'bar']), i)
            user_id = random.choice([1, 2])
            item = Cafe(
                name=name, slug=name, user_id=user_id,
                permission=permission, status=status,
            )
            db.session.add(item)
        db.session.commit()


class TestListCafes(TestCase, CafeMixin):
    def test_list_cafes(self):
        self.create_cafes()
        rv = self.client.get('/api/cafes')
        assert rv.status_code == 200
        value = json.loads(rv.data)
        assert len(value['data']) == 20
        assert 'user' in value['reference']
        assert 'before' in value['cursor']

        rv = self.client.get('/api/cafes?count=40')
        assert rv.status_code == 200
        value = json.loads(rv.data)
        assert 'before' not in value['cursor']


class TestViewCafe(TestCase, CafeMixin):
    def test_not_found(self):
        rv = self.client.get('/api/cafes/notfound')
        assert rv.status_code == 404

    def test_view_cafe(self):
        self.create_cafes(2)
        cafe = Cafe.query.get(1)

        rv = self.client.get('/api/cafes/%s' % cafe.slug)
        value = json.loads(rv.data)
        assert 'user' in value


class TestCafeMembers(TestCase, CafeMixin):

    def create_membership(self, permission, total):
        item = Cafe(
            name='hello', slug='hello', user_id=2,
            permission=permission
        )
        db.session.add(item)
        db.session.commit()
        total = 60

        for i in range(total):
            username = 'demo-%d' % i
            user = User(username=username, email='%s@gmail.com' % username)
            db.session.add(user)
            db.session.commit()
            member = CafeMember(cafe_id=item.id, user_id=user.id)
            member.role = random.choice([
                CafeMember.ROLE_VISITOR,
                CafeMember.ROLE_APPLICANT,
                CafeMember.ROLE_SUBSCRIBER,
                CafeMember.ROLE_MEMBER,
                CafeMember.ROLE_ADMIN,
            ])
            db.session.add(member)
        db.session.commit()

    def test_join_public_cafe(self):
        item = Cafe(
            name='hello', slug='hello', user_id=2,
            permission=Cafe.PERMISSION_PUBLIC,
        )
        db.session.add(item)
        db.session.commit()

        url = '/api/cafes/hello/users'
        headers = self.get_authorized_header(scope='user:subscribe')
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204

        headers = self.get_authorized_header(scope='user:subscribe', user_id=2)
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204

    def test_visitor_join_cafe(self):
        item = Cafe(
            name='hello', slug='hello', user_id=2,
            permission=Cafe.PERMISSION_PUBLIC,
        )
        db.session.add(item)
        # create a visitor membership
        db.session.add(CafeMember(cafe_id=1, user_id=1))
        db.session.commit()

        url = '/api/cafes/hello/users'
        headers = self.get_authorized_header(scope='user:subscribe')
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204

    def test_join_secret_cafe(self):
        item = Cafe(
            name='secret', slug='secret', user_id=1,
            permission=Cafe.PERMISSION_PRIVATE,
        )
        db.session.add(item)
        db.session.commit()

        headers = self.get_authorized_header(scope='user:subscribe', user_id=2)
        url = '/api/cafes/secret/users'
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204

        # already joined
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 204

    def test_leave_cafe(self):
        self.create_cafes(2)
        cafe = Cafe.query.get(2)

        url = '/api/cafes/%s/users' % cafe.slug
        headers = self.get_authorized_header(scope='user:subscribe')
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 404

        item = CafeMember(cafe_id=2, user_id=1)
        db.session.add(item)
        db.session.commit()
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 204

    def test_list_public_cafe_users(self):
        total = 60
        self.create_membership(Cafe.PERMISSION_PUBLIC, total)

        url = '/api/cafes/hello/users'
        rv = self.client.get(url)
        assert rv.status_code == 200

        value = json.loads(rv.data)
        assert 'pagination' in value
        assert value['pagination']['total'] == total
        assert value['pagination']['next'] == 2
        assert value['pagination']['prev'] is None

        url = '/api/cafes/hello/users?page=3'
        rv = self.client.get(url)
        value = json.loads(rv.data)
        assert value['pagination']['prev'] == 2

        rv = self.client.get('/api/cafes/hello/users?page=-1')
        assert rv.status_code == 400
        rv = self.client.get('/api/cafes/hello/users?page=10')
        assert rv.status_code == 400
        rv = self.client.get('/api/cafes/hello/users?perpage=1')
        assert rv.status_code == 400

    def test_list_private_cafe_users_failed(self):
        total = 60
        self.create_membership(Cafe.PERMISSION_PRIVATE, total)

        url = '/api/cafes/hello/users'
        headers = self.get_authorized_header(user_id=1, scope='cafe:private')
        rv = self.client.get(url, headers=headers)
        assert rv.status_code == 403

        headers = self.get_authorized_header(user_id=2)
        rv = self.client.get(url, headers=headers)
        assert rv.status_code == 401

    def test_list_private_cafe_users_success(self):
        total = 60
        self.create_membership(Cafe.PERMISSION_PRIVATE, total)

        url = '/api/cafes/hello/users'
        headers = self.get_authorized_header(user_id=2, scope='cafe:private')
        rv = self.client.get(url, headers=headers)
        assert rv.status_code == 200

        item = CafeMember.query.filter_by(role=CafeMember.ROLE_MEMBER).first()
        headers = self.get_authorized_header(
            user_id=item.user_id, scope='cafe:private',
        )
        rv = self.client.get(url, headers=headers)
        assert rv.status_code == 200


class TestCafeTopics(TestCase):
    def test_list_cafe_topics(self):
        item = Cafe(
            name='hello', slug='hello', user_id=1,
            permission=Cafe.PERMISSION_PUBLIC
        )
        db.session.add(item)
        db.session.commit()

        user_ids = [o.id for o in User.query.all()]

        for i in range(60):
            t = Topic(
                cafe_id=item.id,
                user_id=random.choice(user_ids),
                title='test',
            )
            db.session.add(t)

        db.session.commit()

        rv = self.client.get('/api/cafes/hello/topics')
        assert b'data' in rv.data
