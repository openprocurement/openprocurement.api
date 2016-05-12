Overview
========

The Open Procurement API is the only interface to Open Procurement database
that is core unit of `Open Procurement <http://openprocurement.org/>`_
infrastructure.

The Open Procurement API is a `REST 
<http://en.wikipedia.org/wiki/Representational_State_Transfer>`_-ful
interface that provides programmatic access to Tender database of Open
Procurement system.  It provides predictable URLs for accessing resources,
and uses built-in HTTP features to receive commands and return responses. 
This makes it easy to communicate with.

The API accepts `JSON <http://json.org/>`_ or form-encoded content in
requests.  It returns JSON content in all of its responses, including
errors.  Only the UTF-8 character encoding is supported for both requests
and responses.

Conventions
-----------
All API POST and PUT requests expect a top-level object with a single
element in it named `data`.  Successful responses will mirror this format. 
The data element should itself be an object, containing the parameters for
the request.  In the case of creating a new tender, these are the fields we
want to set on the tender itself.

If the request was successful, we will get a response code of `201`
indicating the object was created.  That response will have a data field at
its top level, which will contain complete information on the new tender,
including its ID.

If something went wrong during the request, we'll get a different status
code and the JSON returned will have an `errors` field at the top level
containing a list of problems.  We look at the first one and print out its
message.

Main responsibilities
---------------------

Business logic
--------------

Project status
--------------

The project has pre alpha status.

The source repository for this project is on GitHub: https://github.com/openprocurement/openprocurement.api

You can leave feedback by raising a new issue on the `issue tracker
<https://github.com/openprocurement/openprocurement.api/issues>`_ (GitHub
registration necessary).  

For general discussion use `Open Procurement
General <https://groups.google.com/group/open-procurement-general>`_
maillist.

General information, roadmap, and technical specifications for the 
Open Procurement project can be found at `openprocurement.org <http://openprocurement.org/en>`_.

Documentation of related packages
---------------------------------

* `Open tender procedure (OpenUA) <http://openua.api-docs.openprocurement.org/en/latest/>`_

* `Open tender procedure with publication in English (OpenEU) <http://openeu.api-docs.openprocurement.org/en/latest/>`_

* `Reporting, negotiation procurement procedure and negotiation procedure for the urgent need  <http://limited.api-docs.openprocurement.org/en/latest/>`_

* `Defense open tender <http://defense.api-docs.openprocurement.org/en/latest/>`_

* `Contracting API interface to OpenProcurement database <http://contracting.api-docs.openprocurement.org/en/latest/>`_


API stability
-------------
API is highly unstable, and while API endpoints are expected to remain
relatively stable the data exchange formats are expected to be changed a
lot.  The changes in the API are communicated via `Open Procurement API
<https://groups.google.com/group/open-procurement-api>`_ maillist.

Change log
----------

0.10
~~~~
Released: not released

 New features:

 - :ref:`Multilot tenders <lots>`


0.9
~~~
Released: not released

 New features:

 - :ref:`MEAT tenders <meat>`


0.8
~~~
Released: 2015-05-12

 New features:

 - Stand-still period for each of the awards independently 
 - Added new cancellation API 

0.7
~~~
Released: 2015-03-13

 New features:

 - Set title, classification and additionalClassifications required
 - Added validation identical cpv groups of items
 - Added upload tender documents by auction user
 - Closing tender by registering contract
 - Strict mode for patching operation
 - Cancalling active award

 Modifications:

 - Authenticated couchdb access
 - Fixed authentication of PUT and PATCH methods
 - Optimized calls to db on start
 - Fixed deliveryLocation fields
 - Fixed edit format field in Documents
 - Fixed restrictions uploading documents of bid

0.6
~~~
Released: 2014-12-15

 New features:

 - Token Broker authorization
 - Actor token authorization
 - Added Item.deliveryLocation
 - Pending complaints Tender completion blocking
 - Rescheduling of failed auctions

0.5
~~~
Released: not released

 New features:

 - Actor token generation
 - Added Item.deliveryAddress
 - Award sequential review logic

 Modifications:

 - Tender.deliveryDate moved to Item.deliveryDate

0.4
~~~
Released: 2014-12-01

 New Features:

 - Filing Complaint on award
 - Complaint attachments
 - Tender Cancelling
 - Question authors visibility

 Modifications:
 
 - Tender status codelist harmonized

0.3
~~~
Released: 2014-11-21

 New Features:

 - Asking Questions
 - Filing Complaint on tender conditions
 - Answer Question
 - Publish Complaint resolution
 - Retrieve Questions and Answers, Complaints and Resolutions
 - Auction Scheduler
 - Auction Runner

 Modifications:

 - :ref:`standard` harmonized with `Open Contracting 1.0RC
   <http://ocds.open-contracting.org/standard/r/1__0__RC/>`_
 - ``/bidders/`` endpoint renamed into ``/bids/``
 - ``modified`` property renamed into ``modificationDate``

0.2
~~~
Released: 2014-11-07

 - Tender Listing Batching (optimized for sync operations)
 - Documents retrieval
 - Change tracking
 - Options: Pretty-print, JSONP
 - Introduction of state machine and time-based state switching

0.1
~~~

Released: 2014-10-24

 - Set up general build, testing, deployment, and ci framework.
 - Creating/modifying tender
 - Adding/modifying/cancelling tender proposal
 - Awarding/disqualification of tender proposals

Next steps
----------
You might find it helpful to look at the :ref:`tutorial`, or the
:ref:`reference`.
