
from flask import json
from werkzeug.exceptions import HTTPException
from werkzeug._compat import text_type


class APIException(HTTPException):
    code = 400
    error = 'invalid_request'

    def __init__(self, code=None, error=None, description=None, response=None):
        if code is not None:
            self.code = code
        if error is not None:
            self.error = error
        super(APIException, self).__init__(description, response)

    def get_body(self, environ=None):
        return text_type(json.dumps(dict(
            error=self.error,
            error_description=self.description,
        )))

    def get_headers(self, environ=None):
        return [('Content-Type', 'application/json')]


class FormError(APIException):
    error = 'invalid_form'

    def __init__(self, form, response=None):
        self.form = form
        super(FormError, self).__init__(None, response)

    def get_body(self, environ=None):
        return text_type(json.dumps(dict(
            error=self.error,
            error_form=self.form.errors,
        )))


class NotAuth(APIException):
    code = 401
    error = 'require_login'
    description = 'Authorization is required'


class NotConfidential(APIException):
    code = 403
    error = 'require_confidential'
    description = 'Only confidential clients are allowed'


class NotFound(APIException):
    code = 404
    error = 'not_found'

    def __init__(self, key):
        description = '%s not found' % key
        super(NotFound, self).__init__(description=description)


class Denied(APIException):
    code = 403
    error = 'permission_denied'

    def __init__(self, key):
        description = 'You have no permission in %s' % key
        super(Denied, self).__init__(description=description)


class Conflict(APIException):
    code = 409
    error = 'conflict'


class InvalidAccount(APIException):
    code = 403
    error = 'invalid_account'
    description = 'Your account is invalid'


class InvalidClient(APIException):
    error = 'invalid_client'
    description = 'Client not found'


class LimitExceeded(APIException):
    code = 429
    error = 'limit_exceeded'
