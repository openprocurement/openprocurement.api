.. Kicking page rebuild 2014-10-30 17:00:08
.. _qualification:

Qualification Operations
========================

When auction is over, the qualification process starts. The status of tender
is `active.qualification` then.  Right after results are submitted to
Central DB, there is award generated for auction winner.

Listing awards
~~~~~~~~~~~~~~

The pending award can be retrieved via request to list all available awards:

.. include:: qualification/awards-get.http
   :code:


When the award is in `pending` status, it means that procuring entity has
to review documents describing the bid and other bidder documents.

Disqualification
~~~~~~~~~~~~~~~~

The protocol of Qualification Committee decision should be uploaded as
document into award and later its status should switch to either `active`
(if it is accepted) or `unsuccessful` (if rejected).

.. include:: qualification/award-pending-upload.http
   :code:

The Qualification Committee can upload several documents, for example, decisions to
prolong the qualification process - in order to allow the bidder to collect all
necessary documents or correct errors.  Such documents would help to have
procedure as transparent as possible and will reduce risk of cancellation by
Complaint Review Body.

.. include:: qualification/award-pending-unsuccessful.http
   :code:

Note that after award rejection the next bid in the value-sorted bid
sequence becomes subject of subsequent award.  For convenience you can use
the `Location` response header from the response above that is pointing
to an award in "pending" state.


Contract Awarding
~~~~~~~~~~~~~~~~~

Protocol upload:

.. include:: qualification/award-protocol-upload.http
   :code:

Confirming the Award:

.. sourcecode:: http

.. include:: qualification/award-pending-active.http
   :code:

The procuring entity can wait until bidder provides all missing documents
(licenses, certificates, statements, etc.) or update original bid documents
to correct errors.  Alternatively, they can reject the bid if provided
documents do not satisfy the pass/fail criteria of tender (even before
full package of supplementary documents is available).

Cancelling Active Award
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes Bidder refuses to sign the contract even after passing
qualification process.  In this case Procuring Entity is expected to be able
to reject approved award and disqualify Bid afterwards.

After we have Award with active status:

.. include:: qualification/award-active-get.http
   :code:

There is need to cancel it:

.. include:: qualification/award-active-cancel.http
   :code:

Note that there is Location header returned that aids in locating the "fresh"
award that is most likely subject for disqualification:

.. include:: qualification/award-active-cancel-upload.http
   :code:

.. include:: qualification/award-active-cancel-disqualify.http
   :code:

In the case when there is another Bid for qualification, there will be
Location header in the response pointing to its Award.


Influence of Complaint Satisfaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If decision of the procuring entity is unfair any bidder can file
complaint and after proper review the whole awarding process can start from
the award in question.

Disqualification decision of procuring entity's qualification committee can be cancelled in the following cases:

* claim for this disqualification has been submitted (claim status is ``claim``);
* claim has been answered (claim status is ``answered``);
* complaint is pending review (complaint status is ``pending``);
* complaint has been satisfied by the Complaint Review Body (complaint status is ``resolved``).

After the disqualification decision cancellation it receives ``cancelled`` status. New pending award is generated and procuring entity is obliged to qualify it again (taking into consideration recommendations from the report of Complaint Review Body if there is one).

.. include:: qualification/awards-unsuccessful-get1.http
   :code:

.. include:: qualification/award-unsuccessful-cancel.http
   :code:

.. include:: qualification/awards-unsuccessful-get2.http
   :code:
