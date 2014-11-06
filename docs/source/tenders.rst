.. Kicking page rebuild 2014-10-30 20:55:46
.. _tenders:

Retrieving Tender Information
=============================

Getting list of all tenders
---------------------------
.. sourcecode:: http

  GET /tenders HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK
 
Reading the individual tender information
-----------------------------------------
.. sourcecode:: http

  GET /tenders/64e93250be76435397e8c992ed4214d1 HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Reading the tender documents list
---------------------------------
.. sourcecode:: http

  GET /tenders/64e93250be76435397e8c992ed4214d1/documents HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Reading the tender document
---------------------------

The document can be retrieved by requesting the url returned in structures
from document list request in `data[*].url`.  It is safe to provide the
download URL to end user for download.
