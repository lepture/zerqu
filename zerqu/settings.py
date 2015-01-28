# coding: utf-8

# Gravatar settings
GRAVATAR_URL = 'https://secure.gravatar.com/avatar/'
GRAVATAR_PARAMETERS = {
    's': '140'
}

# Security settings
ZERQU_VERIFY_SESSION = True

# Available feature choices for a cafe
ZERQU_CAFE_FEATURES = [
    (0, 'text'),
    (1, 'link'),
    (2, 'image'),
    (3, 'video'),
    (4, 'audio'),
    (5, 'gist'),
]
