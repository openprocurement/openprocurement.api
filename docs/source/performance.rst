.. _performance:

Performance recommendations
===========================


Rate Control
-------------

"Aggressive" IP addresses can be restricted in the speed with which servers are processing CDB requests. In this case CDB will respond with :ref:`status code 429 <errors>` to the requests that returned faster than allowed.

Expected client response to such restriction is to repeat requests returned with 429 status code increasing the delay between individual requests sent to the CDB until requests become successful (2xx / 3xx responses).

Such CDB servers behavior is required in order to distribute server resources evenly between clients.