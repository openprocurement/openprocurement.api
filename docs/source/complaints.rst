.. Kicking page rebuild 2014-10-30 17:00:08
.. _complaints:

Complaints Submission
=====================

If tender conditions are favoriting only one provider, or in any other viable case, one can submit Tender Conditions Complaint.

Tender Conditions Complaint Submission
--------------------------------------

.. include:: tutorial/complaint-submission.http
   :code:

Tender Conditions Complaint Retrieval
-------------------------------------

You can list all Tender Conditions Complaints:

.. include:: tutorial/complaints-list.http
   :code:

And check individual complaint:

.. include:: tutorial/complaint.http
   :code:


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
 