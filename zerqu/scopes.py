# coding: utf-8
"""
    zerqu.scopes
    ~~~~~~~~~~~~

    Define available scopes for OAuth.
"""

#: define available scopes
SCOPES = [
    ('user:email', 'read your email address'),
    ('user:write', 'change your account information'),
    ('user:follow', 'follow and unfollow other users'),
    ('user:subscribe', 'follow and unfollow a cafe'),

    ('cafe:private', 'read your private cafes'),
    ('cafe:write', 'create and update your cafes'),

    ('topic:write', 'create topics with your account'),
    ('topic:delete', 'delete your topics'),
    ('comment:write', 'create a comment with your account'),
    ('comment:delete', 'delete your comments'),
]

#: alias scopes
ALIASES = {
    'user': ['user:email', 'user:write', 'user:follow', 'user:subscribe'],
    'cafe': ['cafe:write', 'cafe:private'],
    'topic': ['topic:write', 'topic:delete'],
    'comment': ['comment:write', 'comment:delete'],
}

#: scopes that user can choose to disable
CHOICES = [
    'user:email',
    'cafe:private',
    'topic:delete',
    'comment:delete',
]

#: scopes that user can choose to grant
USER_SCOPES = [
    ('user:email', 'read your email address'),
    ('user:write', 'change your account information'),
    ('user:topic', 'create a topic under your name'),
    ('user:follow', 'follow and unfollow other users'),
    ('user:subscribe', 'follow and unfollow a cafe'),
]


def filter_user_scopes(scopes):
    if 'user' in scopes:
        scopes.remove('user')
        return USER_SCOPES

    rv = []
    for key, desc in USER_SCOPES:
        if key in scopes:
            scopes.remove(key)
            rv.append((key, desc))

    return rv
