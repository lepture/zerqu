# coding: utf-8

import datetime

SITE_NAME = 'ZERQU'
SITE_DESCRIPTION = 'Welcome to ZERQU'
SITE_LINKS = [{'name': 'About', 'url': '/c/about'}]
SITE_YEAR = datetime.date.today().year

ZERQU_CACHE_TYPE = 'simple'
OAUTH2_CACHE_TYPE = 'simple'
ZERQU_REDIS_URI = 'redis://localhost:6379/0'

# Gravatar settings
GRAVATAR_URL = 'https://secure.gravatar.com/avatar/'
GRAVATAR_PARAMETERS = {
    's': '140',
    'd': '404',
}

# ZERQU settings
ZERQU_VERIFY_SESSION = True

ZERQU_APP_HEADER = ''
ZERQU_APP_FOOTER = ''

# user can update topic in the given seconds
ZERQU_VALID_MODIFY_TIME = 3600

# render topic content use the given renderer, other choice is `text`
# it can also be a module string for importing
ZERQU_TEXT_RENDERER = 'markdown'

ZERQU_FEATURE_DEFINES = {
    'link': 0b1,
    'image': 0b10,
    'video': 0b100,
    'audio': 0b1000,
}

# define your custom processors
ZERQU_FEATURE_PROCESSORS = {}

ZERQU_CAFE_CREATOR_ROLE = 4
