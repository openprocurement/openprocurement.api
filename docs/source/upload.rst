.. _upload:

Documents Uploading
===================

All of the document uploading API endpoints follows the same set of rules.

Content-Type: multipart/formdata
--------------------------------

This is normal approach of file uploading defined by `RFC 1867
<http://www.faqs.org/rfcs/rfc1867.html>`_.  The requirements are:

* Form element should have name `file`
* Only one document can be uploaded.

The cURL example::

    curl --form file=@page.pdf http://api-sandbox.openprocurement.org/api/0/tenders/f6882fa63d5141bcabec54a4766eec61/documents

HTTPie example::

    http -f POST http://api-sandbox.openprocurement.org/api/0/tenders/f6882fa63d5141bcabec54a4766eec61/documents file@page.pdf

