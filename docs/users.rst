
Users
======

List all users
~~~~~~~~~~~~~~~

Request with GET method::

    GET /users

Response with::

    {
        "status": "ok",
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
        "status": "ok",
        "data": {
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
    }

Get authenticated user
~~~~~~~~~~~~~~~~~~~~~~

Request with GET method::

    GET /user

Response is the same as getting a single user.


Update the authenticated user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Request with PATCH method::

    PATCH /user

Request with these parameters::

    {
        "bio": "I am a river."
    }

Change password
~~~~~~~~~~~~~~~

Request change username
~~~~~~~~~~~~~~~~~~~~~~~
