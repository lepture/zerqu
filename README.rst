Zerqu
=====

Zerqu is a forum library that provides APIs to create topics, comments and etc.


Development
-----------

Prerequests:

1. VirtualBox
2. Vagrant: https://www.vagrantup.com/downloads.html
3. Ansible: ``pip install ansible``


Install ansible roles::

    $ make install-ansible-roles

Setup vagrant development::

    $ vagrant up
    $ vagrant ssh

Install python requirements in vagrant::

    $ cd /vagrant
    $ source venv/bin/activate
    $ pip install -r deps/requirements.txt

Run app server in vagrant ``/vagrant`` directory::

    $ python app.py

Visit: http://192.168.30.10:5000/
