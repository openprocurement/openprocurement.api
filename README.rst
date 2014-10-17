Documentation
=============

OpenProcurement is initiative to develop software 
powering tenders database and reverse auction.

'openprocurement.api' is component responsible for 
exposing the tenders database to brokers and public.

Documentation about this API is accessible at
http://docs.openprocurement.org/

Building documentation
----------------------

Use following commands to build documentation from `docs/source` into `docs/html`::

 python bootstrap.py -c docs.cfg
 bin/buildout -N -c docs.cfg
 bin/docs

