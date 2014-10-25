.. _bidding:

Bidder Operations
=================

Registration of Bid proposal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/bidders/ HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa607

Uploading Bid documents
~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa607/documents HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa607/documents/bd2e4c64179445cab93987fff3d58d23


Update of proposal
~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  PUT /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Updating Bid documents
~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa607/documents HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa607/documents/bd2e4c64179445cab93987fff3d58d23
  
Cancelling the proposal
~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  DELETE /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Bids Listing
~~~~~~~~~~~~

.. sourcecode:: http

  GET /tenders/64e93250be76435397e8c992ed4214d1/bidders/ HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 200 OK

Retrieving the proposal
~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  GET /tenders/64e93250be76435397e8c992ed4214d1/bidders/4879d3f8ee2443169b5fbbc9f89fa60 HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 200 OK
