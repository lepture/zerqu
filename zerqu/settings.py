# coding: utf-8

import datetime

SITE_NAME = 'ZERQU'
SITE_DESCRIPTION = 'Welcome to ZERQU'
SITE_YEAR = datetime.date.today().year

APP_LINKS = [{'name': 'About', 'url': '/c/about'}]
APP_LOGINS = []
APP_HEADER = ''
APP_FOOTER = ''

OAUTH2_CACHE_TYPE = 'redis'
OAUTH2_CACHE_REDIS_DB = 1
ZERQU_CACHE_TYPE = 'redis'
ZERQU_CACHE_REDIS_DB = 2
ZERQU_REDIS_URI = 'redis://localhost:6379/0'

BABEL_DEFAULT_LOCALE = 'en'
BABEL_LOCALES = ['en', 'zh']

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

ZERQU_CAFE_CREATOR_ROLES = [4, 7, 8, 9]
