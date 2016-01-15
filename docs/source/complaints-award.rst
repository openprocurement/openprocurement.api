.. Kicking page rebuild 2014-10-30 17:00:08

Claim Submission
================

If tender conditions are favoriting only one provider, or in any other viable case, one can submit Tender Award Claim.

Tender Award Claim Submission (with documents)
---------------------------------------------------

At first create a claim:

.. include:: tutorial/award-complaint-submission.http
   :code:

Then upload necessary documents:
   
.. include:: tutorial/award-complaint-submission-upload.http
   :code:

Submit tender conditions claim:
   
.. include:: tutorial/award-complaint-claim.http
   :code:

Tender Award Claim Submission (without documents)
------------------------------------------------------

.. include:: tutorial/award-complaint-submission-claim.http
   :code:

Tender Award Claim/Complaint Retrieval
-------------------------------------------

You can list all Tender Award Claims/Complaints:

.. include:: tutorial/award-complaints-list.http
   :code:

And check individual complaint or claim:

.. include:: tutorial/award-complaint.http
   :code:


Claim's Answer
==============

Answer to resolved claim
------------------------

.. include:: tutorial/award-complaint-answer.http
   :code:


Satisfied Claim
===============

Satisfying resolution
---------------------

.. include:: tutorial/award-complaint-satisfy.http
   :code:


Escalate claim to complaint
---------------------------

.. include:: tutorial/award-complaint-escalate.http
   :code:


Complaint Resolution
====================

Rejecting Tender Award Complaint
-------------------------------------

.. include:: tutorial/award-complaint-reject.http
   :code:


Submitting Tender Award Complaint Resolution
-------------------------------------------------

The Complaint Review Body uploads the resolution document:

.. include:: tutorial/award-complaint-resolution-upload.http
   :code:

And either resolves complaint:

.. include:: tutorial/award-complaint-resolve.http
   :code:

Or declines it:

.. include:: tutorial/award-complaint-decline.http
   :code:
 