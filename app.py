# coding: utf-8

import os
import logging
from zerqu import create_app
from zerqu.models import db

logger = logging.getLogger('flask_oauthlib')
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

root = os.path.abspath(os.path.dirname(__file__))
os.environ['ZERQU_CONF'] = os.path.join(root, 'etc/development.py')

app = create_app()
with app.app_context():
    db.create_all()
app.debug = True
app.run()
