# coding: utf-8

from zerqu.models import db, User, OAuthClient

users = [
    ('zerqu', 'hello@zerqu', None, 10),
    ('test', 'test@zerqu', 'test-password', 1),
]
clients = [
]


def run():
    for username, email, password, status in users:
        user = User(username=username, email=email, status=status)
        if password:
            user.password = password
        db.session.add(user)
    db.session.commit()

    client = OAuthClient(
        user_id=1,
        name='iOS App',
        client_id='ios',
        client_secret='secret',
        is_confidential=True,
        _redirect_uris='http://localhost/oauth',
    )
    db.session.add(client)
    db.session.commit()
