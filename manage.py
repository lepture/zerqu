# coding: utf-8
from __future__ import print_function
import os

from flask.ext.script import Manager

from zerqu import create_app
from zerqu.models.base import db
from zerqu.models.user import User


CONFIG = os.path.abspath('./local_config.py')

app = create_app(CONFIG)
manager = Manager(app)


@manager.command
def adduser(username, password, role=User.ROLE_ACTIVE, **kwargs):
    """Used to add new user into database.
    Usage::
        $ python manage.py adduser YOUR_USERNAME YOUR_PASSWORD [--role=YOUR_ROLE]

    :param username: requied as username of new user.
    :param password: requied as password of new user.
    :param role: role of new user which should be 1, 4, 7, 8, 9 or -4.
                 Greater indicates more powerful.
    """
    userdata = dict(username=username, password=password, role=role)
    userdata.update(kwargs)
    user = User(**userdata)

    with app.app_context():
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            print('==== Add user failed! ====')
            print(e)
            db.session.rollback()
        else:
            print('New user: {username} with password {password} '
                  'and role {role}'.format(**userdata))


if __name__ == '__main__':
    manager.run()
