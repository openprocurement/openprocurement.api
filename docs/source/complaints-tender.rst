.. Kicking page rebuild 2014-10-30 17:00:08

Claim Submission
================

If tender conditions are favoriting particular supplier, or in any other viable case, anyone can submit Tender Conditions Claim.

Tender Conditions Claim Submission (with documents)
---------------------------------------------------

At first create a claim:

.. include:: complaints/complaint-submission.http
   :code:

Then upload necessary documents:

.. include:: complaints/complaint-submission-upload.http
   :code:

Submit tender conditions claim:

.. include:: complaints/complaint-claim.http
   :code:

Tender Conditions Claim Submission (without documents)
------------------------------------------------------

Create claim that does not need additional documents:

.. include:: complaints/complaint-submission-claim.http
   :code:

Tender Conditions Claim/Complaint Retrieval
-------------------------------------------

You can list all Tender Conditions Claims/Complaints:

.. include:: complaints/complaints-list.http
   :code:

And check individual complaint or claim:

.. include:: complaints/complaint.http
   :code:


Claim's Answer
==============

Answer to resolved claim
------------------------

.. include:: complaints/complaint-answer.http
   :code:


Satisfied Claim
===============

Satisfying resolution
---------------------

.. include:: complaints/complaint-satisfy.http
   :code:


Escalate claim to complaint
---------------------------

.. include:: complaints/complaint-escalate.http
   :code:


Complaint Resolution
====================

Rejecting Tender Conditions Complaint
-------------------------------------

.. include:: complaints/complaint-reject.http
   :code:


Submitting Tender Conditions Complaint Resolution
-------------------------------------------------

The Complaint Review Body uploads the resolution document:

.. include:: complaints/complaint-resolution-upload.http
   :code:

And either resolves complaint:

.. include:: complaints/complaint-resolve.http
   :code:

Or declines it:

.. include:: complaints/complaint-decline.http
   :code:
