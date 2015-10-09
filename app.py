# coding: utf-8

import sys
import logging
from zerqu import create_app
from zerqu.models import db


app = create_app({'DEBUG': True})


def show_verbose_log():
    formatter = logging.Formatter(
        '[%(levelname)s %(funcName)s %(filename)s:%(lineno)d]: %(message)s'
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    log = logging.getLogger('flask_oauthlib')
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    log = logging.getLogger('oauthlib')
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)


def create_database():
    import fixtures
    with app.app_context():
        db.drop_all()
        db.create_all()
        fixtures.run()


if '--initdb' in sys.argv:
    create_database()
    sys.exit()


with app.app_context():
    db.create_all()

app.run(host='0.0.0.0')
