.. _cluster:

API in cluster mode
===================

There is a cluster of several servers that synchronize data between each other. Client should always work with the same server to ensure consistency between separate requests to the CDB. That is why cookie is required while sending POST/PUT/PATCH/DELETE requests. Cookies provide server stickiness. You can get such cookie via GET request and then use it for POST/PUT/PATCH/DELETE.


If during operations the server requested by cookie went down or is unavailable, client will receive :ref:`status code 412 <errors>` of request and new cookie to use. Request should be repeated with new cookie.
