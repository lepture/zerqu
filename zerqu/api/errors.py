
from flask import json
from werkzeug.exceptions import HTTPException
from werkzeug._compat import text_type


class APIException(HTTPException):
    code = 400
    error_code = 'invalid_request'

    def __init__(self, code=None, error=None, description=None, response=None):
        if code is not None:
            self.code = code
        if error is not None:
            self.error_code = error
        super(APIException, self).__init__(description, response)

    def get_body(self, environ=None):
        return text_type(json.dumps(dict(
            error_code=self.error_code,
            error_description=self.description,
        )))

    def get_headers(self, environ=None):
        return [('Content-Type', 'application/json')]


class NotFound(APIException):
    code = 404
    error_code = 'not_found'

    def __init__(self, key, response=None):
        description = '%s not found' % key
        super(NotFound, self).__init__(None, None, description, response)


def first_or_404(model, **kwargs):
    data = model.cache.filter_first(**kwargs)
    if data:
        return data
    key = model.__name__
    if len(kwargs) == 1:
        key = '%s "%s"' % (key, list(kwargs.values())[0])
    raise NotFound(key)


class Denied(APIException):
    code = 403
    error_code = 'permission_denied'

    def __init__(self, key, response=None):
        description = 'You have no permission in %s' % key
        super(Denied, self).__init__(None, None, description, response)
