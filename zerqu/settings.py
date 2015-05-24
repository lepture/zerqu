# coding: utf-8

import datetime

SITE_NAME = 'ZERQU'
SITE_YEAR = datetime.date.today().year

ZERQU_CACHE_TYPE = 'simple'
OAUTH2_CACHE_TYPE = 'simple'

# Gravatar settings
GRAVATAR_URL = 'https://secure.gravatar.com/avatar/'
GRAVATAR_PARAMETERS = {
    's': '140'
}

# ZERQU settings
ZERQU_VERIFY_SESSION = True

ZERQU_BROWSER_TEMPLATE = 'browser.html'
ZERQU_BROWSER_STYLES = []
ZERQU_BROWSER_SCRIPTS = []

ZERQU_MOBILE_TEMPLATE = 'mobile.html'
ZERQU_MOBILE_STYLES = []
ZERQU_MOBILE_SCRIPTS = []

# user can update topic in the given seconds
ZERQU_VALID_MODIFY_TIME = 600

# render topic content use the given renderer, other choice is `text`
# it can also be a module string for importing
ZERQU_TEXT_RENDERER = 'markdown'

ZERQU_CAFE_FEATURES = {
    'link': 0b1,
    'image': 0b10,
    'gist': 0b100,
    'video': 0b1000,
    'audio': 0b10000,
}

ZERQU_CAFE_CREATOR_ROLE = 4
