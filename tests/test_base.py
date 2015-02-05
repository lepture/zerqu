# coding: utf-8

from zerqu.versions import API_VERSION
from ._base import TestCase


class TestAPI(TestCase):
    def test_get_api_index(self):
        rv = self.client.get('/api/')
        assert API_VERSION in rv.data
