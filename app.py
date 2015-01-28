# coding: utf-8

import os
from zerqu import create_app
from zerqu.models import db

root = os.path.abspath(os.path.dirname(__file__))

app = create_app(os.path.join(root, 'etc/development.py'))
with app.app_context():
    db.create_all()
app.debug = True
app.run()
