.. Kicking page rebuild 2014-10-30 17:00:08

Claim/Complaint Retrieval
=========================

Tender Conditions Claim/Complaint Retrieval
-------------------------------------------

You can list all Tender Conditions Claims/Complaints:

.. include:: complaints/complaints-list.http
   :code:

And check individual complaint or claim:

.. include:: complaints/complaint.http
   :code:


Claim Submission
================

If tender conditions are favoriting particular supplier, or in any other viable case, any registered user can submit Tender Conditions Claim.

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


Disagreement with decision
--------------------------

.. include:: complaints/complaint-escalate.http
   :code:
