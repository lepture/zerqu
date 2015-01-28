coverage:
	@coverage run --branch --source=zerqu -m py.test tests
	@coverage html
