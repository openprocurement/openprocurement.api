.. _2pc:

2 Phase Commit
==============

.. _tender-2pc:

The 2-phase commit provides a mechanism for CDB to publish only the tenders that clients are able to control and duplicates of which they have rights to cancel.
 
The reason for duplicated tenders can be cases when the requester did not receive a response from the server about tender creation and, therefore, repeated the request. Removing such tenders requires administrative intervention.

Creating tender with 2 Phase Commit
-----------------------------------

Sending a single-phase request for a tender creation (POST /tenders) according to the "old" mechanism, that creates a tender already in the ``active.enquiries`` status:

.. include:: tutorial/tender-post-attempt-json-data.http
   :code:

Mechanism of the 2-phase commit
--------------------------------

Tender becomes available after the successful completion of the following requests:

1. Creation of the tender in the ``draft`` status.
2. Transfer of the tender to ``active.enquiries`` status through a separate request (publication).


Creation of a tender
~~~~~~~~~~~~~~~~~~~~

A request `POST /tenders` creates a tender in status ``draft``. As a result, an ``acc_token`` is passed for the further tender management. 

.. include:: tutorial/tender-post-2pc.http
   :code:

Validation rules in the ``draft`` status:

* ``enquiryPeriod.startDate`` can be empty;
* ``enquiryPeriod.startDate`` can not be in the past;
* ``enquiryPeriod.startDate`` is not automatically generated.


Tender with the ``draft`` status is "invisible" in the `GET /tenders` list. Chronograph does not "see" it, therefore, does not switch statuses.


Publication of a tender
~~~~~~~~~~~~~~~~~~~~~~~

The request `PATCH /tenders/{id}?acc_token=...`  ``{“data”:{“status”:”active.enquiries”}}`` changes status of tender (according to the request), therefore, publishes it ("visualizes" it in the `GET /tenders list`).

.. include:: tutorial/tender-patch-2pc.http
   :code:
   
All tenders created in the CDB but not yet published will not be displayed on the web platform and, therefore, will not lead to their announcement.

Repeating of the request for publication in case of problem with receiving a response from the server will not cause errors.

The new mechanism is available along with the "old" one. The "old" is likely to be turned off in one of the later releases.


Example of incorrectly formed request error
-------------------------------------------

Error indicates that the data is not found in the body of JSON.

.. include:: tutorial/tender-post-attempt-json.http
   :code:

