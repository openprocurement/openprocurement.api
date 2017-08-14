.. Kicking page rebuild 2014-10-30 17:00:08

Claim/Complaint Retrieval
=========================

Tender Award Claim/Complaint Retrieval
-------------------------------------------

You can list all Tender Award Claims/Complaints:

.. include:: complaints/award-complaints-list.http
   :code:

And check individual complaint or claim:

.. include:: complaints/award-complaint.http
   :code:

Claim Submission
================

If tender award is favoriting only one supplier, or in any other viable case, participants can submit Tender Award Claim.

Tender Award Claim Submission (with documents)
---------------------------------------------------

At first create a claim. Send POST request with bidder's access token.

.. include:: complaints/award-complaint-submission.http
   :code:

Then upload necessary documents:

.. include:: complaints/award-complaint-submission-upload.http
   :code:

Submit tender award claim:

.. include:: complaints/award-complaint-claim.http
   :code:

Tender Award Claim Submission (without documents)
------------------------------------------------------

You can submit claim that does not need additional documents:

.. include:: complaints/award-complaint-submission-claim.http
   :code:

Claim's Answer
==============

Answer to resolved claim
------------------------

.. include:: complaints/award-complaint-answer.http
   :code:


Satisfied Claim
===============

Satisfying resolution
---------------------

.. include:: complaints/award-complaint-satisfy.http
   :code:


Disagreement with decision
--------------------------

.. include:: complaints/award-complaint-escalate.http
   :code:
