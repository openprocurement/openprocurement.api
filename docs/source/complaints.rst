.. Kicking page rebuild 2014-10-30 17:00:08
.. _complaints:


..
    contents:: Table of Contents
   :depth: 2
   :local:

Complaint Workflow
==================

For more detailed information read `Non-price criteria <http://openprocurement.org/en/nonprice-criteria.html>`_.

Workflow
--------

.. image:: complaint_w.png
   :alt: Complaint workflow

Roles
-----

:Complainant:
    dashed

:Tender owner:
    plain

:Reviewer:
    bold

:Chronograph:
    dotted

Statuses
--------

:draft:
    initial status

    Complainant can cancel claim, upload documents and submit claim.

:claim:
    Tender owner can upload documents and answer to claim.

    Complainant can cancel claim.

:answered:
    Complainant can cancel claim, upload documents, admit solution or escalate claim to complaint.

:pending:
    Reviewer can upload documents and review complaint.

    Complainant can cancel claim.

:invalid:
    terminal status

    Complaint recognized as invalid.

:declined:
    terminal status

    Complaint recognized as declined.

:resolved:
    terminal status

    Complaint recognized as resolved.

:cancelled:
    terminal status

    Complaint cancelled by complainant.


Claims Submission
=================

If tender conditions are favoriting only one provider, or in any other viable case, one can submit Tender Conditions Complaint.

Tender Conditions Claim Submission with documents
-------------------------------------------------

.. include:: tutorial/complaint-submission.http
   :code:

.. include:: tutorial/complaint-submission-upload.http
   :code:

.. include:: tutorial/complaint-claim.http
   :code:

Tender Conditions Claim Submission without documents
----------------------------------------------------

.. include:: tutorial/complaint-submission-claim.http
   :code:

Tender Conditions Complaint Retrieval
-------------------------------------

You can list all Tender Conditions Complaints:

.. include:: tutorial/complaints-list.http
   :code:

And check individual complaint:

.. include:: tutorial/complaint.http
   :code:

..
    Tender Award Complaint Submission
    ---------------------------------

    .. include:: tutorial/award-complaint-submission.http
    :code:

    Tender Award Complaint Retrieval
    --------------------------------

    You can list all complaints:

    .. include:: tutorial/award-complaints-list.http
    :code:

    And check individual complaint:

    .. include:: tutorial/award-complaint.http
    :code:


Claims Answer
=============

Answer to resolved claim
------------------------

.. include:: tutorial/complaint-answer.http
   :code:


Claims Satisfy
==============

Satisfying resolution
---------------------

.. include:: tutorial/complaint-satisfy.http
   :code:


Escalate claim to complaint
---------------------------

.. include:: tutorial/complaint-escalate.http
   :code:


Complaints Resolution
=====================

Rejecting Tender Conditions Complaint
-------------------------------------

.. include:: tutorial/complaint-reject.http
   :code:


Submitting Tender Conditions Complaint Resolution
-------------------------------------------------

The Complaint Review Body uploads the resolution document:

.. include:: tutorial/complaint-resolution-upload.http
   :code:

And either resolves complaint:

.. include:: tutorial/complaint-resolve.http
   :code:

Or declines it:

.. include:: tutorial/complaint-decline.http
   :code:

..
    Rejecting Tender Award Complaint
    --------------------------------

    .. include:: tutorial/award-complaint-reject.http
    :code:

    Submitting Tender Award Complaint Resolution
    --------------------------------------------
    
    .. include:: tutorial/award-complaint-resolution-upload.http
    :code:

    .. include:: tutorial/award-complaint-resolve.http
    :code:

    .. include:: tutorial/award-complaint-decline.http
    :code:
 