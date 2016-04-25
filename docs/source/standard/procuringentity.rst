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
    string
    
    Type of procuring entity

    Possible values:
        - ``general`` - Procuring entity (general)
        - ``special`` - Procuring entity that operates in certain spheres of economic activity
        - ``defense`` - Procuring entity that conducts procurement for the defense needs
        - ``other`` -  Legal persons that are not procuring entities in the sense of the Law, but are state, utility, public enterprises, economic partnerships or associations of enterprises in which state or public utility share is 50 percent or more

