Response Format
===============

API response will be in **application/json** format. Every response will have
a **status** and **data** section::

    {
        "status": "ok",
        "data": {}
    }


Status
------

A status indicates if the response is correct. Here is a success response::

    {
        "status": "ok"
    }

An error response will have an **error_code** and **error_description**::

    {
        "status": "error",
        "error_code": "invalid_token",
        "error_description": "Token is expired"
    }

Data
----

The **data** section contains the actual data you want. It may be an array or
a hash. If you requests a list of things, it is an array . If you request a
single item, it is a hash map.

A hash map data looks like::

    {
        "status": "ok",
        "data": {
            "id": 1,
            "key": "value"
        }
    }

An array data response looks like::

    {
        "status": "ok",
        "data": [
            {
                "id": 1,
                "key": "value"
            },
            {
                "id": 2,
                "key": "value"
            }
        ]
    }


Meta
----

Meta data is an additional information for data response. For example::

    {
        "status": "ok",
        "data": [
            {
                "id": 1,
                "user_id": 1
            }
        ],
        "meta": {
            "user_id": {
                "1": {
                    "username": "zerqu"
                }
            }
        }
    }

In this example, the **user_id** in data is an ID, you can use the ID to get
the full information of the user in **meta** section.

Pagination
----------

Pagination is useful when a single array data response can not hold all the
data. In this case, you can fetch the next page::

    {
        "status": "ok",
        "data": [],
        "pagination": {
            "total": 121,
            "perpage": 20,
            "page": 1,
            "pages": 7,
            "prev": null,
            "next": 2
        }
    }

Request pagination with parameters **page**. For example::

    GET /api/resource?page=2

Cursor
------

Cursor is another efficient to fetch data. When a single array data response
can not hold all the data::

    {
        "status": "ok",
        "data": [],
        "cursor": {
            "key": "id",
            "before": 1,
            "after": 30
        }
    }

An array data response will always return with a **pagination** or **cursor**.
