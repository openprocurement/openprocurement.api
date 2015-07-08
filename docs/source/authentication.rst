.. _authentication:

Authentication
==============

Some of the API requests (especially the ones that are read-only GET
requests) do not require any authenication.  The other ones, that modify data
into the database, require broker authentication via API key.  Additionally,
owner tokens are issued to facilitate multiple actor roles upon object creation.

API keys
--------

API key is username to use with Basic Authenication scheme.

Owner tokens
------------

Getting token
~~~~~~~~~~~~~

The token is issued when object is created in the database:

.. include:: tutorial/create-tender-procuringEntity.http
   :code:

You can see the `access` with `token` in response.  Its value can be used to
modify objects further under "Owner role".  

Using token
~~~~~~~~~~~

You can pass access token in the following ways:

1) `acc_token` URL query string parameter
2) `X-Access-Token` HTTP request header
3) `access.token` in the body of POST/PUT/PATCH request

See the example of the action with token passed as URL query string:

.. include:: tutorial/patch-items-value-periods.http
   :code:
