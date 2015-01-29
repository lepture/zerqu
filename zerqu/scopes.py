# coding: utf-8
"""
    zerqu.scopes
    ~~~~~~~~~~~~

    Define available scopes for OAuth.
"""

PUBLIC_SCOPES = [
]

#: scopes that user can choose to grant
USER_SCOPES = [
    ('user:email', 'read your email address'),
    ('user:write', 'change your account information'),
    ('user:topic', 'create a topic under your name'),
    ('user:follow', 'follow and unfollow other users'),
    ('user:subscribe', 'follow and unfollow a cafe'),
]

#: scopes that only available for confidential clients
CONFIDENTIAL_SCOPES = [
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
