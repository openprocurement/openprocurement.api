.. image:: https://travis-ci.org/openprocurement/openprocurement.api.svg?branch=master
    :target: https://travis-ci.org/openprocurement/openprocurement.api

.. image:: https://coveralls.io/repos/openprocurement/openprocurement.api/badge.png
  :target: https://coveralls.io/r/openprocurement/openprocurement.api

.. image:: https://readthedocs.org/projects/openprocurementapi/badge/?version=latest
    :target: http://api-docs.openprocurement.org/

Documentation
=============

OpenProcurement is initiative to develop software 
powering tenders database and reverse auction.

'openprocurement.api' is component responsible for 
exposing the tenders database to brokers and public.

Documentation about this API is accessible at
http://api-docs.openprocurement.org/

Building documentation
----------------------

Use following commands to build documentation from `docs/source` into `docs/html`::

 python bootstrap.py -c docs.cfg
 bin/buildout -N -c docs.cfg
 bin/docs

