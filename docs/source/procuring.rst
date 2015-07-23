.. Kicking page rebuild 2014-10-30 17:00:08
.. _procuring:

Procuring Entity Operations
===========================

Registration of the Tender
--------------------------
Tender registration consists of primary record creation and documentation uploading.

Creating primary Tender record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When registering tender in the database, one has provide all primary tender details (except binary documents) in payload of request.
   
.. sourcecode:: http

  POST /tenders HTTP/1.1

The produced response will contain URL of the created tender in Location header of response, and in ``data.id`` of body.
  
.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1

.. _procuring-uploading-docs:

Uploading documentation
~~~~~~~~~~~~~~~~~~~~~~~

All tender documentation should be uploaded with the following request - one request
per document. You can see supported request types in :ref:`upload` section.

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/documents HTTP/1.1

The response produced will have URL of the tender uploaded document in Location header of response and in ``data.id`` of body.

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/documents/6a7d13bd8ec449e08882aeb92180d938

Example request:

.. include:: tutorial/upload-tender-notice.http
   :code:

Changing the Tender
-------------------
Procuring Entity can change both the primary record and associated documentation. 

.. If Tenders state does not allow such change the request will fail with Unauthorized response.

Changing primary Tender Record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Procuring Entity can change the Tender properties with the following request. Data to change should be in payload of the message.

.. sourcecode:: http

  PATCH /tenders/64e93250be76435397e8c992ed4214d1 HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Changing existing documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Procuring Entity can upload new versions of the tender documentation. You
can see supported request types in :ref:`upload` section.

.. sourcecode:: http

  PUT /tenders/64e93250be76435397e8c992ed4214d1/documents/6a7d13bd8ec449e08882aeb92180d938 HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Example request:

.. include:: tutorial/update-award-criteria.http
   :code:

Uploading additional documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The same as :ref:`procuring-uploading-docs`.
