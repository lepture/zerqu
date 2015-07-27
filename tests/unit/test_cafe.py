# coding: utf-8

from zerqu.models import db, Cafe, CafeMember
from ._base import TestCase


class TestCafeMember(TestCase):
    def create_cafe_membership(self):
        pub = Cafe(
            slug='hello', name='hello', user_id=2,
            permission=Cafe.PERMISSION_PUBLIC
        )
        db.session.add(pub)
        db.session.flush()
        pri = Cafe(
            slug='world', name='world', user_id=2,
            permission=Cafe.PERMISSION_PRIVATE
        )
        db.session.add(pri)
        db.session.flush()
        db.session.add(CafeMember(
            user_id=1, cafe_id=pub.id,
            role=CafeMember.ROLE_MEMBER,
        ))
        db.session.add(CafeMember(
            user_id=1, cafe_id=pri.id,
            role=CafeMember.ROLE_MEMBER,
        ))
        db.session.commit()

    def test_get_user_following_cafe_ids(self):
        self.create_cafe_membership()
        rv = CafeMember.get_user_following_cafe_ids(1)
        assert len(rv) == 2

    def test_get_user_following_public_cafe_ids(self):
        self.create_cafe_membership()
        rv = CafeMember.get_user_following_public_cafe_ids(1)
        assert len(rv) == 1
