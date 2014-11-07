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

The request itself should look like::

    POST /api/0.2/tenders/f6882fa63d5141bcabec54a4766eec61/documents HTTP/1.1
    Content-Type: multipart/form-data; boundary=28e02f7d4a3c4da19c4e2589329ad36f
    Host: api-sandbox.openprocurement.org

    --28e02f7d4a3c4da19c4e2589329ad36f
    Content-Disposition: form-data; name="file"; filename="page.pdf"

    ..Contents of PDF goes here...
    --28e02f7d4a3c4da19c4e2589329ad36f--
