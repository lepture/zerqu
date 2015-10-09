# coding: utf-8

import sys
import logging
from zerqu import create_app
from zerqu.models import db

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

app = create_app({
    'SECRET_KEY': 'secret',
    'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres@localhost/development'
})


def create_database():
    import fixtures
    with app.app_context():
        db.drop_all()
        db.create_all()
        fixtures.run()


if '--initdb' in sys.argv:
    create_database()
    sys.exit()

app.debug = True
app.run(host='0.0.0.0')
