coverage:
	@coverage run --branch --source=zerqu -m py.test tests
	@coverage html


babel-update:
	@pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
	@pybabel update -i messages.pot -d zerqu/translations && find zerqu/translations -name "*.swp" -delete


babel-compile:
	@pybabel compile -d zerqu/translations


install-ansible-roles:
	@ansible-galaxy install -r playbooks/requirements.yml -p playbooks/roles


install:
	@sudo /var/venv/bin/pip install -r deps/requirements.txt

run:
	@ZERQU_CONF=/vagrant/local_config.py /var/venv/bin/python app.py
