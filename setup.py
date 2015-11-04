#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def fread(filename):
    with open(filename) as f:
        return f.read()

basic_requires = [
    'Flask==0.10.1',
    'Flask-WTF==0.11',
    'Flask-OAuthlib==0.9.1',
    'Flask-Mail==0.9.1',

    # renderer
    'mistune==0.7',
    'Pygments==2.0.2',

    # database
    'redis==2.10.3',
    'psycopg2==2.6.1',
    'SQLAlchemy==1.0.6',
    'Flask-SQLAlchemy==2.0',

    # Babel
    'Flask-Babel==0.9',
    'Babel==2.0',
    'pytz==2015.4',
]
enhance_requires = [
    # enhance json
    'simplejson==3.6.5',

    # enhance redis
    'hiredis==0.2.0',

    # enhance requests
    'pyOpenSSL==0.15.1',
    'ndg-httpsclient==0.4.0',
    'pyasn1==0.1.8',
]


setup(
    name='zerqu',
    version='0.1',
    author='Hsiaoming Yang',
    author_email='me@lepture.com',
    packages=find_packages(exclude=['tests', 'tests.*']),
    description="An API based forum-like application",
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    long_description=fread('README.rst'),
    license='unknown',
    install_requires=basic_requires + enhance_requires,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
