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
API is highly unstable, and while API endpoint are expecetd to remain
relatively stable the data exchange formats are expected to be changed a
lot.  The changes in the API are communicated via `Open Procurement API
<https://groups.google.com/group/open-procurement-api>`_ maillist.

Change log
----------
0.1
~~~

Released: Not yet.

 - Set up general build, testing, deployment, and ci framework.

Next steps
----------
You might find it helpful to look at the :ref:`tutorial`, or the
:ref:`reference`.
