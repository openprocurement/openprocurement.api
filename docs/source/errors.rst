.. _errors:

Responses
=========

After processing API is always providing response, reporting either success
or failure.

Codes
-----
In all cases, the API should return an `HTTP Status Code
<http://en.wikipedia.org/wiki/List_of_HTTP_status_codes>`_ that indicates
the nature of the failure (below), with a response body in JSON format
containing additional information.

200
  Success. If data was requested, it will be available in the `data` field
  at the top level of the response body.

201
  Success (for object creation). Its information is available in the `data`
  field at the top level of the response body.  The API URL where the object
  can be retrieved is also returned in the `Location` header of the
  response.

400
  Invalid request. This usually occurs because of a missing or malformed
  parameter.  Check the documentation and the syntax of your request and try
  again.

401
  No authorization. A valid API key was not provided with the request, so
  the API could not associate a user with the request.

403
  Forbidden. The API key and request syntax was valid but the server is
  refusing to complete the request.  This can happen if you try to read or
  write to objects or properties that the party does not have access to.

404
  Not found. Either the request method and path supplied do not specify a
  known action in the API, or the object specified by the request does not
  exist.

429
  Rate Limit Enforced.

500
  Server error. There was a problem on OpenProcurement's end.

Contents
--------
In the event of an error, the response body will contain an `errors` field
at the top level.  This contains an array of at least one error object,
described below:

message
  *totalValue.amount: Missing input* - Message providing more detail about the
  error that occurred, if available.

messageUID
  Unique message id. Will stay the same even if content of the message can
  change, depending on other parameters.

*id*
  Unique correlation identifier of the error response for audit and issue
  reporting purposes.

Example Response
~~~~~~~~~~~~~~~~
Sample below indicate incomplete request.

.. sourcecode:: http

  HTTP/1.1 400 Missing input

  {
    "message":"totalValue.amount: Missing input",
    "messageUID":"e6cfac20-4497-4b36-bae8-7048133d9d07",
    "id":"4468eee5-9820-4d51-adee-a245a2fb6ee5"
  }
