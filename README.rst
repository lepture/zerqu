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
    $ make install

Run app server in vagrant ``/vagrant`` directory::

    $ make run

Visit: http://192.168.30.10:5000/
