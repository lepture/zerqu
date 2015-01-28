# coding: utf-8

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

# Available feature choices for a cafe
ZERQU_CAFE_FEATURES = [
    (0, 'text'),
    (1, 'link'),
    (2, 'image'),
    (3, 'video'),
    (4, 'audio'),
    (5, 'gist'),
]
