.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Organization, Company

.. _Organization:

Organization
============

Schema
------

:name:
    string, multilingual
:identifier:
    :ref:`Identifier`
:additionalIdentifiers:
    List of :ref:`identifier` objects
:address:
    :ref:`Address`
:contactPoint:
    :ref:`ContactPoint`


.. index:: Company, id

.. _Identifier:

Identifier
==========

Schema
------

:scheme:
   string

   |ocdsDescription|
   Organization identifiers be drawn from an existing identification scheme. 
   This field is used to indicate the scheme or codelist in which the
   identifier will be found.  This value should be drawn from the
   Organization Identifier Scheme.

:id:
   string
   
   |ocdsDescription| The identifier of the organization in the selected scheme.

:legalName:
   string, multilingual

   |ocdsDescription|
   The legally registered name of the organization.

:uri:
   uri

   |ocdsDescription|
   A URI to identify the organization, such as those provided by Open
   Corporates or some other relevant URI provider.  This is not for listing
   the website of the organization: that can be done through the url field
   of the Organization contact point.


.. index:: Address, City, Street, Country

.. _Address:

Address
=======

Schema
------

:streetAddress:
    string
:locality:
    string
:region:
    string
:postalCode:
    string
:countryName:
    string


.. index:: Person, Phone, Email, Website, ContactPoint

.. _ContactPoint:

ContactPoint
============

Schema
------

:name:
    string, multilingual
:email:
    email
:telephone:
    string
:faxNumber:
    string
:url:
    url
