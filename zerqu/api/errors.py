
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


class NotAuth(APIException):
    code = 401
    error_code = 'authorization_required'

    def __init__(self, description=None):
        if description is None:
            description = 'Authorization is required'
        super(NotAuth, self).__init__(description=description)


class NotConfidential(APIException):
    code = 403
    error_code = 'confidential_only'

    def __init__(self, description=None):
        if description is None:
            description = 'Only confidential clients are allowed'
        super(NotConfidential, self).__init__(description=description)


class NotFound(APIException):
    code = 404
    error_code = 'not_found'

    def __init__(self, key):
        description = '%s not found' % key
        super(NotFound, self).__init__(description=description)


class Denied(APIException):
    code = 403
    error_code = 'permission_denied'

    def __init__(self, key):
        description = 'You have no permission in %s' % key
        super(Denied, self).__init__(description=description)


class Conflict(APIException):
    code = 409
    error_code = 'conflict'

    def __init__(self, description):
        super(Conflict, self).__init__(description=description)


class InvalidAccount(Denied):
    error_code = 'invalid_account'

    def __init__(self, description=None):
        if description is None:
            description = 'Your account is invalid'
        super(Denied, self).__init__(description=description)
