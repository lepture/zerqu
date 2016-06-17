Zerqu
=====

Zerqu is a forum library that provides APIs to create topics, comments and etc.


Development
-----------

Using Vagrant
~~~~~~~~~~~~~

Prerequests:

1. VirtualBox
2. Vagrant: https://www.vagrantup.com/downloads.html
3. Ansible: ``pip install ansible``


Install ansible roles::

    $ make install-ansible-roles

Setup vagrant development::

    $ vagrant up
    $ vagrant ssh

Install python requirements in vagrant and create database::

    $ cd /vagrant
    $ make install
    $ make database

Run app server in vagrant ``/vagrant`` directory::

    $ make run

Visit: `http://192.168.30.10:5000/`

The docker way
~~~~~~~~~~~~~~

You can also run zerqu in docker.

Prerequests:

1. docker
2. docker-compose

Build docker containers::

    $ docker-compose up

Initiate database schema::

    $ docker-compose run web bash -c "ZERQU_CONF=/code/local_config.py alembic upgrade head"

Visit: `http://localhost:5000`
