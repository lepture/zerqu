# coding: utf-8

import os
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

root = os.path.abspath(os.path.dirname(__file__))
os.environ['ZERQU_CONF'] = os.path.join(root, 'etc/development.py')

app = create_app()
with app.app_context():
    db.create_all()
app.debug = True
app.run()
