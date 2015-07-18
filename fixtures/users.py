
import random
from werkzeug.security import gen_salt
from zerqu.models import User


def iter_admin_users():
    yield {
        "id": 1,
        "username": "root",
        "email": "root@zerqu.com",
        "reputation": 1000,
        "role": 9
    }

    yield {
        "id": 2,
        "username": "lepture",
        "email": "me@lepture.com",
        "reputation": 1000,
        "role": 8
    }


def iter_normal_users():
    domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']

    for i in range(3, 1024):
        name = gen_salt(random.randint(4, 20)).lower()
        yield {
            "id": i,
            "username": name,
            "email": "%s@%s" % (name, random.choice(domains)),
            "reputation": random.randint(0, 100),
            "role": random.choice([-9, 0, 4]),
        }


def iter_data():
    for data in iter_admin_users():
        user = User(**data)
        user.password = 'zerqu'
        yield user
    for data in iter_normal_users():
        yield User(**data)
