# coding: utf-8

from zerqu.libs.ratelimit import ratelimit
from zerqu.libs.utils import is_robot, is_mobile
from ._base import TestCase


class TestRateLimit(TestCase):
    def test_ratelimit(self):
        remaining, expires = ratelimit('test:ratelimit', 20, 20)
        assert remaining == 19
        assert expires == 20

        for i in range(20):
            remaining, expires = ratelimit('test:ratelimit', 20, 20)
        assert remaining == 0


class TestUserAgent(TestCase):
    def test_is_robot(self):
        app = self.app

        @app.route('/test-is-robot')
        def is_robot_view():
            if is_robot():
                return 'yes'
            return 'no'

        rv = self.client.get('/test-is-robot', headers={
            'User-Agent': 'Googlebot-Image/1.0'
        })
        assert b'yes' == rv.data

    def test_is_mobile(self):
        ua = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) '
            'AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 '
            'Mobile/10A5376e Safari/8536.25'
        )
        app = self.app

        @app.route('/test-is-mobile')
        def is_mobile_view():
            if is_mobile():
                return 'yes'
            return 'no'

        rv = self.client.get('/test-is-mobile', headers={'User-Agent': ua})
        assert b'yes' == rv.data
