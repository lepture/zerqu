Authentication
==============

Authentication through Ajax and OAuth.

Login via Ajax
--------------

Create new session with POST::

    POST /session

    {
        "username": "your_username",
        "password": "your_password",
        "permanent": true
    }

If username and password matched, server will create a session cookie::

    {
        "id": 1,
        "username": "your_username",
        "..": "...."
    }

Logout via Ajax
---------------

Logout with DELETE request::

    DELETE /session

Server will delete and destroy the session cookie, response with::

    {
        "redirect_uri": "/"
    }


OAuth login and logout
----------------------

It's just OAuth 2, request tokens at::

    POST /oauth/token
