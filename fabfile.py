# coding: utf-8

from fabric.api import env
from fabric.api import sudo, run, cd, local, put

env.use_ssh_config = True
env.keepalive = 60


def upload():
    run('mkdir -p /var/zerqu')

    local('python setup.py sdist --formats=gztar', capture=False)
    dist = local('python setup.py --fullname', capture=True).strip()
    put('dist/%s.tar.gz' % dist, '/var/zerqu/pack.tar.gz')

    with cd('/var/zerqu'):
        run('tar xzf /var/zerqu/pack.tar.gz')
        sudo('mv %s src' % dist)
