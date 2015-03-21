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


def extend_scopes(scopes):
    rv = []
    for name in scopes:
        if name in ALIASES:
            rv.extend(ALIASES[name])
        else:
            rv.append(name)
    return rv
