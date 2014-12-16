.. _authentication:

Authentication
==============

Some of the API requests (especially the ones that are read-only GET
requests do not require any authenication.  The other ones, that modify data
into the database require broker authentication via API key.  Additionally
to facilitate multiple actor roles upon objct creation there are owner
tokens issued.

API keys
--------

API key is username to use with Basic Authenication scheme.

Owner tokens
------------

The token is issued when object is created in the database:

.. include:: tutorial/create-tender-procuringEntity.http
   :code:

You can see the `access` with `token` in response.  Its value can be used to
modify objects further under "Owner role":
