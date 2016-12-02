.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Feature

.. _Feature:

Feature
=======

Schema
------

:code:
    string, auto-generated

    Code of the feature.

:featureOf:
    string, required

    Possible values are:

    * `tenderer`
    * `lot`
    * `item`

:relatedItem:
    string

    Id of related :ref:`item` or :ref:`lot` (only if the ``featureOf`` value is ``item`` or ``lot``).

:title:
    string, multilingual, required

    Title of the feature.

:description:
    string, multilingual

    Description of the feature.

:enum:
    list

    List of values:

    :value:
        float, required

        Value of the feature.

    :title:
        string, multilingual, required

        Title of the value.

    :description:
        string, multilingual

        Description of the value.
