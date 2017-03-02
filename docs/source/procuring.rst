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

.. include:: tutorial/tender-post-attempt-json-data.http
   :code:

The produced response will contain URL of the created tender in Location header of response, and in ``data.id`` of body.

.. _procuring-uploading-docs:

Uploading documentation
~~~~~~~~~~~~~~~~~~~~~~~

All tender documentation should be uploaded with the following request - one request
per document. You can see supported request types in :ref:`upload` section.

.. include:: tutorial/upload-tender-notice.http
   :code:

The response produced will have URL of the tender uploaded document in Location header of response and in ``data.id`` of body.

Upload another document:

.. include:: tutorial/upload-award-criteria.http
   :code:

Changing the Tender
-------------------
Procuring Entity can change both the primary record and associated documentation.

.. If Tenders state does not allow such change the request will fail with Unauthorized response.

Changing primary Tender Record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Procuring Entity can change the Tender properties with the following request. Data to change should be in payload of the message.

.. include:: tutorial/patch-items-value-periods.http
   :code:

Changing existing documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Procuring Entity can upload new versions of the tender documentation. You
can see supported request types in :ref:`upload` section.

.. include:: tutorial/update-award-criteria.http
   :code:

Uploading additional documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The same as :ref:`procuring-uploading-docs`.
