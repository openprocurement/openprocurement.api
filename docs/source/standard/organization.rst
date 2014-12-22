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
    :ref:`Address`, required
:contactPoint:
    :ref:`ContactPoint`, required


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
   string, required
   
   |ocdsDescription| The identifier of the organization in the selected
   scheme.

   The allowed codes are the ones found in `"Organisation Registration Agency"
   codelist of IATI
   Standard <http://iatistandard.org/codelists/OrganisationRegistrationAgency/>`_
   with addition of `UA-EDR` code for organizations registered in Ukraine
   (EDRPOU and IPN).

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
    string, required


.. index:: Person, Phone, Email, Website, ContactPoint

.. _ContactPoint:

ContactPoint
============

Schema
------

:name:
    string, multilingual, required
:email:
    email
:telephone:
    string
:faxNumber:
    string
:url:
    url

Either `email` or `telephone` fields have to be provided.
