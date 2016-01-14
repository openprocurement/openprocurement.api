.. Kicking page rebuild 2014-10-30 17:00:08

Claim Submission
================

If tender conditions are favoriting only one provider, or in any other viable case, one can submit Tender Conditions Claim.

Tender Conditions Claim Submission (with documents)
---------------------------------------------------

At first create a claim:

.. include:: tutorial/complaint-submission.http
   :code:

Then upload necessary documents:
   
.. include:: tutorial/complaint-submission-upload.http
   :code:

Submit tender conditions claim:
   
.. include:: tutorial/complaint-claim.http
   :code:

Tender Conditions Claim Submission (without documents)
------------------------------------------------------

.. include:: tutorial/complaint-submission-claim.http
   :code:

Tender Conditions Claim/Complaint Retrieval
-------------------------------------------

You can list all Tender Conditions Claims/Complaints:

.. include:: tutorial/complaints-list.http
   :code:

And check individual complaint or claim:

.. include:: tutorial/complaint.http
   :code:


Claim's Answer
==============

Answer to resolved claim
------------------------

.. include:: tutorial/complaint-answer.http
   :code:


Satisfied Claim
===============

Satisfying resolution
---------------------

.. include:: tutorial/complaint-satisfy.http
   :code:


Escalate claim to complaint
---------------------------

.. include:: tutorial/complaint-escalate.http
   :code:


Complaint Resolution
====================

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
 