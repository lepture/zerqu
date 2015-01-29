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
    ('user:email', 'Grant access to read your email address'),
    ('user:write', 'Grant access to change your account information'),
    ('user:topic', 'Grant access to create a topic'),
    ('user:follow', 'Grant access to follow and unfollow other users'),
    ('user:subscribe', 'Grant access to follow and unfollow a cafe'),
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
