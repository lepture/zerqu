# coding: utf-8

from zerqu.models.webpage import sanitize_link


def test_sanitize_link():
    assert sanitize_link('lepture.com') == 'http://lepture.com'
    assert sanitize_link('https://lepture.com') == 'https://lepture.com'
    rv = sanitize_link('http://lepture.com/?utm_source=yuehu')
    assert rv == 'http://lepture.com/'
