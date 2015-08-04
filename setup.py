#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def fread(filename):
    with open(filename) as f:
        return f.read()

flask_requires = [
    'Flask',
    'Flask-WTF',
    'Flask-OAuthlib',
    'Flask-SQLAlchemy',
    'Flask-Mail',
]
zerqu_requires = [
    'Pygments',
    'mistune',
    'redis',
    'psycopg2',
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
    install_requires=flask_requires + zerqu_requires,
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
