import os
import json
from zerqu.models import db, User

root = os.path.dirname(__file__)


def load(cls, filename):
    with open(os.path.join(root, filename), 'rb') as f:
        data = json.load(f)

    for kw in data:
        db.session.add(cls(**kw))

    db.session.commit()


def run():
    load(User, 'users.json')
