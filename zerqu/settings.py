# coding: utf-8

import datetime

SITE_NAME = 'ZERQU'
SITE_DESCRIPTION = 'Welcome to ZERQU'
SITE_LINKS = [{'name': 'About', 'url': '/c/about'}]
SITE_YEAR = datetime.date.today().year

SITE_LOGINS = []
SITE_HEADER = ''
SITE_FOOTER = ''

RATE_LIMITER_TYPE = 'redis'
OAUTH2_CACHE_TYPE = 'redis'
OAUTH2_CACHE_REDIS_DB = 1
ZERQU_CACHE_TYPE = 'redis'
ZERQU_CACHE_REDIS_DB = 2
ZERQU_REDIS_URI = 'redis://localhost:6379/0'

BABEL_DEFAULT_LOCALE = 'en'
BABEL_LOCALES = ['en', 'zh']

# Gravatar settings
GRAVATAR_URL = 'https://secure.gravatar.com/avatar/'
GRAVATAR_PARAMETERS = {
    's': '140',
    'd': '404',
}

# ZERQU settings

# ZERQU_AVATAR_BASE = 'https://secure.gravatar.com/'

# async fetching mode
ZERQU_ASYNC = False
ZERQU_VERIFY_SESSION = True

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
