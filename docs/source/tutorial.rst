.. _tutorial:

Tutorial
========

Exploring basic rules
---------------------

Let's try exploring the `/tenders` endpoint:

.. include:: tutorial/initial-tender-listing.http
   :code:

Just invoking it reveals empty set.

Now let's attempt creating some tender:

.. include:: tutorial/tender-post-attempt.http
   :code:

Error states that only accepted Content-Type is `application/json`.

Let's satisfy the Content-type requirement:

.. include:: tutorial/tender-post-attempt-json.http
   :code:

Error states that no `data` found in JSON body.


.. index:: Tender

Creating tender
---------------

Let's provide the data attribute in the body submitted:

.. include:: tutorial/tender-post-attempt-json-data.http
   :code:

Success! Now we can see that new object was created. Response code is `201`
and `Location` response header reports the location of object created.  The
body of response reveals the information about tender created, its internal
`id` (that matches the `Location` segment), its official `tenderID` and
`modified` datestamp stating the moment in time when tender was last
modified.  Note that tender is created with `active.enquiries` status.

Let's access the URL of object created (the `Location` header of the response):

.. include:: tutorial/blank-tender-view.http
   :code:

.. XXX body is empty for some reason (printf fails)

We can see the same response we got after creating tender. 

Let's see what listing of tenders reveals us:

.. include:: tutorial/tender-listing.http
   :code:

We do see the internal `id` of a tender (that can be used to construct full URL by prepending `http://api-sandbox.openprocurement.org/api/0/tenders/`) and its `modified` datestamp.

Let's try creating tender with more data, passing the `procuringEntity` of a tender:

.. include:: tutorial/create-tender-procuringEntity.http
   :code:

And again we have `201 Created` response code, `Location` header and body wth extra `id`, `tenderID`, and `modified` properties.

Let's check what tender registry contains:

.. include:: tutorial/tender-listing-after-procuringEntity.http
   :code:

And indeed we have 2 tenders now.


Modifying tender
----------------

Let's update tender by providing it with all other essential properties:

.. include:: tutorial/patch-items-value-periods.http
   :code:

.. XXX body is empty for some reason (printf fails)

We see the added properies merged with existing data of tender. Additionally the `modified` property updated to reflect the last modification datestamp.

Checking the listing again reflects the new modification date:

.. include:: tutorial/tender-listing-after-patch.http
   :code:


.. index:: Document

Uploading documentation
-----------------------

Procuring entity can upload PDF files into tender created. Uploading should
follow the :ref:`upload` rules.

.. include:: tutorial/upload-tender-notice.http
   :code:

`201 Created` response code and `Location` header confirm document creation. 
We can additionally query the `documents` collection API endpoint to confirm the
action:

.. include:: tutorial/tender-documents.http
   :code:

The single array element describes the document uploaded. We can upload more documents:

.. include:: tutorial/upload-award-criteria.http
   :code:

And again we can confirm that there are two documents uploaded.

.. include:: tutorial/tender-documents-2.http
   :code:

In case we made an error, we can reupload the document over the older version:

.. include:: tutorial/update-award-criteria.http
   :code:

And we can see that it is overriding the original version:

.. include:: tutorial/tender-documents-3.http
   :code:


.. index:: Enquiries, Question, Answer

Enquiries
---------

When tender is in `active.enquiry` status, interested parties can ask questions:

.. include:: tutorial/ask-question.http
   :code:

Bidder is answering them:

.. include:: tutorial/answer-question.http
   :code:

And one can retrieve the questions list:

.. include:: tutorial/list-question.http
   :code:

And individual answer:

.. include:: tutorial/get-answer.http
   :code:


.. index:: Bidding

Registering bid
---------------

When ``Tender.tenderingPeriod.startDate`` comes Tender switches to `tendering` status that allows registration of bids.

Bidder can register a bid:

.. include:: tutorial/register-bidder.http
   :code:

And upload proposal document:

.. include:: tutorial/upload-bid-proposal.http
   :code:

It is possible to check documents uploaded:

.. include:: tutorial/bidder-documents.http
   :code:

For best effect (biggest economy) Tender should have multiple bidders registered:

.. include:: tutorial/register-2nd-bidder.http
   :code:


.. index:: Awarding, Qualification

Confirming qualification
------------------------

Qualification comission registers its decision via following call:

.. include:: tutorial/confirm-qualification.http
   :code:

Canceling tender
----------------

Tender creator can cancel tender anytime:

.. include:: tutorial/cancel-tender.http
   :code:

