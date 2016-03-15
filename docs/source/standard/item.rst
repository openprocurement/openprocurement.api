.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Item, Parameter, Classification, CPV, Unit

.. _Item:

Item
====

Schema
------

:id:
    string, auto-generated

:description:
    string, multilingual, required

    |ocdsDescription|
    A description of the goods, services to be provided.

:classification:
    :ref:`Classification`

    |ocdsDescription|
    The primary classification for the item. See the
    itemClassificationScheme to identify preferred classification lists,
    including CPV and GSIN.

    It is mandatory for `classification.scheme` to be `CPV`. The
    `classification.id` should be valid CPV code.

:additionalClassifications:
    List of :ref:`Classification` objects

    |ocdsDescription|
    An array of additional classifications for the item. See the
    itemClassificationScheme codelist for common options to use in OCDS. 
    This may also be used to present codes from an internal classification
    scheme.

    It is mandatory to have at least one item with `ДКПП` as `scheme`.

:unit:
    :ref:`Unit`

    |ocdsDescription| 
    Description of the unit which the good comes in e.g.  hours, kilograms. 
    Made up of a unit name, and the value of a single unit.

:quantity:
    integer

    |ocdsDescription|
    The number of units required

:deliveryDate:
    :ref:`Period`

    Period during which the item should be delivered.

:deliveryAddress:
    :ref:`Address`

    Address, where the item should be delivered.

:deliveryLocation:
    dictionary

    Geographical coordinates of delivery location. Element consist of the following items:

    :latitude:
        string, required
    :longitude:
        string, required
    :elevation:
        string, optional, usually not used

    `deliveryLocation` usually takes precedence over `deliveryAddress` if both are present.

:relatedLot:
    string

    Id of related :ref:`lot`.


.. _Classification:

Classification
==============

Schema
------

:scheme:
    string

    |ocdsDescription|
    A classification should be drawn from an existing scheme or list of
    codes.  This field is used to indicate the scheme/codelist from which
    the classification is drawn.  For line item classifications, this value
    should represent a known Item Classification Scheme wherever possible.

:id:
    string

    |ocdsDescription|
    The classification code drawn from the selected scheme.

:description:
    string

    |ocdsDescription|
    A textual description or title for the code.

:uri:
    uri

    |ocdsDescription|
    A URI to identify the code. In the event individual URIs are not
    available for items in the identifier scheme this value should be left
    blank.

.. _Unit:

Unit
====

Schema
------

:code:
    string, required

    UN/CEFACT Recommendation 20 unit code.

:name:
    string

    |ocdsDescription|
    Name of the unit