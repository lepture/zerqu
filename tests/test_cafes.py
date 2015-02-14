# coding: utf-8

import random
from flask import json
from zerqu.models import db, Cafe, CafeMember
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
            status = random.choice(Cafe.STATUS.keys())
            name = '%s-%d' % (random.choice(['foo', 'bar']), i)
            user_id = random.choice([1, 2])
            item = Cafe(
                name=name, slug=name, user_id=user_id,
                permission=permission, status=status,
            )
            db.session.add(item)
        db.session.commit()


class TestListCafes(TestCase, CafeMixin):
    def test_list_without_parameters(self):
        self.create_cafes()
        rv = self.client.get('/api/cafes')
        assert rv.status_code == 200
        value = json.loads(rv.data)
        assert len(value['data']) == 20
        assert 'user_id' in value['meta']


class TestViewCafe(TestCase, CafeMixin):
    def test_not_found(self):
        rv = self.client.get('/api/cafes/notfound')
        assert rv.status_code == 404

    def test_view_cafe(self):
        self.create_cafes(2)
        cafe = Cafe.query.get(1)

        rv = self.client.get('/api/cafes/%s' % cafe.slug)
        value = json.loads(rv.data)
        assert 'user' in value['data']


class TestCafeMembers(TestCase, CafeMixin):
    def test_join_public_cafe(self):
        item = Cafe(
            name='hello', slug='hello', user_id=2,
            permission=Cafe.PERMISSION_PUBLIC,
        )
        db.session.add(item)
        db.session.commit()

        url = '/api/cafes/hello/users'
        headers = self.get_authorized_header(scope='user:follow')
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 200

        headers = self.get_authorized_header(scope='user:follow', user_id=2)
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 200

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
        headers = self.get_authorized_header(scope='user:follow')
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 200

    def test_join_secret_cafe(self):
        item = Cafe(
            name='secret', slug='secret', user_id=1,
            permission=Cafe.PERMISSION_PRIVATE,
        )
        db.session.add(item)
        db.session.commit()

        headers = self.get_authorized_header(scope='user:follow', user_id=2)
        url = '/api/cafes/secret/users'
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 200

        # already joined
        rv = self.client.post(url, headers=headers)
        assert rv.status_code == 200

    def test_leave_cafe(self):
        self.create_cafes(2)
        cafe = Cafe.query.get(2)

        url = '/api/cafes/%s/users' % cafe.slug
        headers = self.get_authorized_header(scope='user:follow')
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 404

        item = CafeMember(cafe_id=2, user_id=1)
        db.session.add(item)
        db.session.commit()
        rv = self.client.delete(url, headers=headers)
        assert rv.status_code == 200
