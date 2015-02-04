# coding: utf-8

from zerqu.versions import API_VERSION


def test_get_api_index(client):
    rv = client.get('/api/')
    assert API_VERSION in rv.data
