Overview
========

The Open Procurement API is the only interface to Open Procurement database
that is core unit of `Open Procurement <http://openprocurement.org/>`_
infrastructure.

The Open Procurement API is `REST 
<http://en.wikipedia.org/wiki/Representational_State_Transfer>`_-ful
interface, providing programmatic access to Tender database of Open
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
code and the JSON returned will contain an `errors` field at the top level
containing a list of problems.  We look at the first one and print out its
message.

Main responsibilities
---------------------

Business logic
--------------

Project status
--------------

The project has pre alpha status.

The source repository for this project is on GitHub:

https://github.com/openprocurement/openprocurement.api

You can leave feedback by raising a new issue on the `issue tracker
<https://github.com/openprocurement/openprocurement.api/issues>`_ (GitHub
registration necessary).  For general discussion use `Open Procurement
General <https://groups.google.com/group/open-procurement-general>`_
maillist.

API stability
-------------
API is highly unstable, and while API endpoints are expected to remain
relatively stable the data exchange formats are expected to be changed a
lot.  The changes in the API are communicated via `Open Procurement API
<https://groups.google.com/group/open-procurement-api>`_ maillist.

Change log
----------
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
