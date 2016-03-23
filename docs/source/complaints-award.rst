.. Kicking page rebuild 2014-10-30 17:00:08

Claim Submission
================

If tender conditions are favoriting only one supplier, or in any other viable case, participants can submit Tender Award Claim.

Tender Award Claim Submission (with documents)
---------------------------------------------------

At first create a claim. Send POST request with bidder's access token.

.. include:: complaints/award-complaint-submission.http
   :code:

Then upload necessary documents:

.. include:: complaints/award-complaint-submission-upload.http
   :code:

Submit tender conditions claim:

.. include:: complaints/award-complaint-claim.http
   :code:

Tender Award Claim Submission (without documents)
------------------------------------------------------

You can submit claim that does not need additional documents:

.. include:: complaints/award-complaint-submission-claim.http
   :code:

Tender Award Claim/Complaint Retrieval
-------------------------------------------

You can list all Tender Award Claims/Complaints:

.. include:: complaints/award-complaints-list.http
   :code:

And check individual complaint or claim:

.. include:: complaints/award-complaint.http
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


Escalate claim to complaint
---------------------------

.. include:: complaints/award-complaint-escalate.http
   :code:


Complaint Resolution
====================

Rejecting Tender Award Complaint
-------------------------------------

.. include:: complaints/award-complaint-reject.http
   :code:


Submitting Tender Award Complaint Resolution
-------------------------------------------------

The Complaint Review Body uploads the resolution document:

.. include:: complaints/award-complaint-resolution-upload.http
   :code:

And either resolves complaint:

.. include:: complaints/award-complaint-resolve.http
   :code:

Or declines it:

.. include:: complaints/award-complaint-decline.http
   :code:
