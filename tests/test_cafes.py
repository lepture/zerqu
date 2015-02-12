# coding: utf-8

import random
from flask import json
from zerqu.models import db, Cafe
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
                _permission=permission, status=status,
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
