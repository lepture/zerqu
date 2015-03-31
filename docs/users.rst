
Users
======

List all users
~~~~~~~~~~~~~~~

Request with GET method::

    GET /users

Response with::

    {
        "data": [{
            "id": 1,
            "username": "huashan",
            "avatar_url": "https://example.com/avatar/1.png",
            "role": "staff",
            "is_active": true,
            "url": "http://zerqu.com/",
            "description": "I am a mountain.",
            "reputation": 10,
            "created_at": "2014-12-31T14:40:52Z",
            "updated_at": "2014-12-31T18:50:06Z"
        }],
        "pagination": {}
    }


Get a single user
~~~~~~~~~~~~~~~~~

Request with GET method::

    GET /users/{{username}}

Response with::

    {
        "id": 1,
        "username": "huashan",
        "avatar_url": "https://example.com/avatar/1.png",
        "role": "admin",
        "active": true,
        "url": "http://zerqu.com/",
        "bio": "I am a mountain.",
        "created_at": "2014-12-31T14:40:52Z",
        "updated_at": "2014-12-31T18:50:06Z"
    }

Get authenticated user
~~~~~~~~~~~~~~~~~~~~~~

Request with GET method:

.. sourcecode:: http

    GET /api/users/me HTTP/1.1
    Host: example.com
    Accept: application/vnd.zerqu+json; version=1
    Authorization: Bearer QNPh7UPkfaKwcpr1fKAzvA72q9Os7y

Response with:

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "id": 1,
      "username": "zerqu",
      "description": null,
      "avatar_url": "https://example.com/avatar/zerqu",
      "is_active": true,
      "label": "staff",
      "reputation": 10,
      "created_at": "2015-02-27T09:24:23Z",
      "updated_at": "2015-02-27T09:24:23Z"
    }


Response is the same as getting a single user.


Update the authenticated user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Request with PATCH method::

    PATCH /users/me

Request with these parameters::

    {
        "bio": "I am a river."
    }

Change password
~~~~~~~~~~~~~~~

Request change username
~~~~~~~~~~~~~~~~~~~~~~~
