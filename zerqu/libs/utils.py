# coding: utf-8

from flask import request

ROBOT_BROWSERS = ('google', 'msn', 'yahoo', 'ask', 'aol')
MOBILE_PLATFORMS = ('iphone', 'android', 'wii')


def is_robot():
    return request.user_agent.browser in ROBOT_BROWSERS


def is_mobile():
    return request.user_agent.platform in MOBILE_PLATFORMS


def is_json():
    if request.is_xhr:
        return True

    if request.path.startswith('/api/'):
        return True

    if hasattr(request, 'oauth_client'):
        return True

    if request.accept_mimetypes.accept_json:
        return True

    return False
