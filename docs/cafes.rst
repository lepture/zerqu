Cafes
=====

A cafe is the place where you can have a discussion with your friends.


List all cafes
~~~~~~~~~~~~~~

Request with GET method::

    GET /cafes

Response with::

    {
        "data": [{
            "id": 30,
            "slug": "support",
            "name": "Tech Support",
            "description": "",
            "base_color": "",
            "text_color": "",
            "background_color": "",
            "background_url": "",
            "logo_url": "",
            "is_active": true,
            "count": {
                "topic": 20,
                "users": 31
            },
            "user": {
                "id": 1,
                "username": "huashan",
                "avatar_url": "https://example.com/avatar/1.png",
                "role": "admin",
                "active": true,
                "url": "http://doocer.com/",
                "bio": "I am a mountain.",
                "reputation": 10,
                "created_at": "2014-12-31T14:40:52Z",
                "updated_at": "2014-12-31T18:50:06Z"
            },
            "created_at": "2014-12-31T14:40:52Z",
            "updated_at": "2014-12-31T18:50:06Z"
        }],
        "cursor": 20
    }


Get a single cafe
~~~~~~~~~~~~~~~~~

Request with GET method::

    GET /cafes/{{slug}}

Response with::

    {
        "data": {
            "slug": "support",
            "name": "Tech Support",
            "description": "",
            "base_color": "",
            "text_color": "",
            "background_color": "",
            "background_url": "",
            "logo_url": "",
            "active": true,
            "count": {
                "topic": 20,
                "users": 3100
            },
            "user": {
                "id": 1,
                "username": "lepture",
                "avatar_url": "https://example.com/avatar/1.png",
                "role": "admin",
                "active": true,
                "url": "http://lepture.com/",
                "bio": "I am a mountain.",
                "reputation": 10,
                "created_at": "2014-12-31T14:40:52Z",
                "updated_at": "2014-12-31T18:50:06Z"
            },
            "created_at": "2014-12-31T14:40:52Z",
            "updated_at": "2014-12-31T18:50:06Z"
        }
    }
