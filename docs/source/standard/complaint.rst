.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Complaint, dispute

.. _complaint:

Complaint
=========

Schema
------

:id:
    uid, auto-generated

:author:
    :ref:`Organization`, required

    Organization filing a complaint (contactPoint - person, identification - organization that person represents).

:title:
    string, required

    Title of the complaint.

:description:
    Description of the issue.

:date:
    string, :ref:`date`, auto-generated

    Date of posting.

:dateSubmitted:
    string, :ref:`date`, auto-generated

    Date when claim was submitted.

:dateAnswered:
    string, :ref:`date`, auto-generated

    Date when Procuring entity answered the claim.

:dateEscalated:
    string, :ref:`date`, auto-generated

    Date of claim to complaint escalation.

:dateDecision:
    string, :ref:`date`, auto-generated

    Date of complaint decision.

:dateCanceled:
    string, :ref:`date`, auto-generated

    Date of cancelling.

:status:
    string

    Possible values are:

    * `draft`
    * `claim`
    * `answered`
    * `pending`
    * `invalid`
    * `declined`
    * `resolved`
    * `cancelled`

:type:
    string

    Possible values of type are:

    * `claim`
    * `complaint`

:resolution:
    string

    Resolution of Procuring entity.

:resolutionType:
    string

    Possible values of resolution type are:

    * `invalid`
    * `declined`
    * `resolved`

:satisfied:
    bool

    Claim is satisfied?

:decision:
    string

    Reviewer decision.

:cancellationReason:
    string

    Cancellation reason.

:documents:
    List of :ref:`Document` objects

:relatedLot:
    string

    Id of related :ref:`lot`.

:tendererAction:
    string

    Tenderer action.

:tendererActionDate:
    string, :ref:`date`, auto-generated

    Date of tenderer action.
