import os
import json
from zerqu.models import db
from zerqu.models import (
    OAuthClient,
)


root = os.path.dirname(__file__)


def load(cls, filename):
    with open(os.path.join(root, filename), 'rb') as f:
        data = json.load(f)

    for kw in data:
        db.session.add(cls(**kw))

    db.session.commit()


def commit(module):
    for m in module.iter_data():
        db.session.add(m)
    db.session.commit()


def run():
    from fixtures import users, cafes
    commit(users)
    commit(cafes)

    load(OAuthClient, 'clients.json')
