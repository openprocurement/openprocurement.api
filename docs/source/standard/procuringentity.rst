.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: ProcuringEntity

.. _ProcuringEntity:

ProcuringEntity
===============

Schema
------

:name:
    string, multilingual

    |ocdsDescription|
    The common name of the organization.

:identifier:
    :ref:`Identifier`

    |ocdsDescription|
    The primary identifier for this organization.

:additionalIdentifiers:
    List of :ref:`identifier` objects

:address:
    :ref:`Address`, required

:contactPoint:
    :ref:`ContactPoint`, required

:kind:
    string, Type of customer

    choices:
        'general' - Customer (general)
        'special' - The customer that operates in specific areas of management
        'defense' - Customer carrying out procurement for defense
        'other' -  Legal persons who are not customers in the sense of the law, but are state, municipal, public enterprises, economic societies or associations of enterprises in which state or municipal share is 50 percent or more
