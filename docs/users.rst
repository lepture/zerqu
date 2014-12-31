
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
            "screen_name": "Huashan Mountain",
            "avatar_url": "https://example.com/avatar/1.png",
            "role": "admin",
            "active": true,
            "url": "http://doocer.com/",
            "bio": "I am a mountain.",
            "reputation": 10,
            "created_at": "2014-12-31T14:40:52Z",
            "updated_at": "2014-12-31T18:50:06Z"
        }]
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
            "screen_name": "Huashan Mountain",
            "avatar_url": "https://example.com/avatar/1.png",
            "role": "admin",
            "active": true,
            "url": "http://doocer.com/",
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
        "screen_name": "Wu Yue"
    }

Change password
~~~~~~~~~~~~~~~

Request change username
~~~~~~~~~~~~~~~~~~~~~~~
