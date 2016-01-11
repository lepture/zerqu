# coding: utf-8
import unittest

from zerqu.libs import renderer
from zerqu.libs.ratelimit import ratelimit
from zerqu.libs.utils import is_robot, is_mobile
from zerqu.libs.webparser import parse_meta
from zerqu.libs.errors import LimitExceeded
from ._base import TestCase


class TestRateLimit(TestCase):
    def test_ratelimit(self):
        remaining, expires = ratelimit('test:ratelimit', 20, 20)
        assert remaining == 19
        assert expires == 20

        for i in range(18):
            remaining, expires = ratelimit('test:ratelimit', 20, 20)

        with self.assertRaises(LimitExceeded):
            ratelimit('test:ratelimit', 20, 20)


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


class TestRenderer(TestCase):
    def test_markdown_image(self):
        img = 'hello ![alt](http://path.to/img)'
        assert '<figure>' not in renderer.render_markdown(img, code=False)

        img = 'hello ![alt](http://path.to/img "has title")'
        assert '<figure>' in renderer.render_markdown(img, code=False)

    def test_markdown_code(self):
        s = '```\nprint()\n```'
        assert 'highlight' not in renderer.render_markdown(s, code=True)

        s = '```python\nprint()\n```'
        assert 'highlight' in renderer.render_markdown(s, code=True)

    def test_text(self):
        s = 'hello\nword\n\nnewline'
        assert '<p>' in renderer.render_text(s)
        assert '<br>' in renderer.render_text(s)


class TestParser(unittest.TestCase):
    def test_parse_meta(self):
        link = u'http://fabric-chs.readthedocs.org/zh_CN/chs/'
        rsp = u'''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>欢迎访问 Fabric 中文文档 &mdash; Fabric  文档</title>
<link rel="top" title="Fabric  文档" href="#" />
<link rel="next" title="概览 &amp; 教程" href="tutorial.html" />
</head>
<body role="document">
</body>
</html>
'''
        meta = parse_meta(rsp, link)
        assert u'—' in meta[u'title']
        assert u'&mdash;' not in meta[u'title']
