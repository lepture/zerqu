Cafes
=====

A cafe is the place where you can have a discussion with your friends.


List all cafes
~~~~~~~~~~~~~~

Request with GET method::

    GET /cafes

Response with::

    {
        "status": "ok",
        "data": [
        ]
    }


Get a single cafe
~~~~~~~~~~~~~~~~~

Request with GET method::

    GET /cafes/{{slug}}

Response with::

    {
        "status": "ok",
        "data": {
            "slug": "support",
            "name": "Tech Support",
            "description": "",
            "base_color": "",
            "text_color": "",
            "background_color": "",
            "background_url": "",
            "logo_url": "",
            "feature": "audio",
            "active": true,
            "count": {
                "topic": 20,
                "users": 3100
            },
            "created_by": 1,
            "created_at": "2014-12-31T14:40:52Z",
            "updated_at": "2014-12-31T18:50:06Z"
        }
    }


Create a cafe
~~~~~~~~~~~~~

Available features:

0. text: nothing, just a text topic
1. link: a linked topic
2. audio: you can create an audio topic in this cafe
3. video: you can create a video topic in this cafe
4. image: you can create an image topic in this cafe
5. gist: you can insert a gist in this cafe
