.. Kicking page rebuild 2014-10-30 17:00:08
.. _qualification:

Qualification Operations
========================

When auction is over the qualification process starts. The status of tender
is `active.qualification` then.  Right after results are submitted to
Central DB, there is award generated for auction winner.

Listing awards
~~~~~~~~~~~~~~

The pending award can be retrieved via request to list all awards available:

.. sourcecode:: http

  GET /tenders/64e93250be76435397e8c992ed4214d1/awards

The award is with `pending` status meaning the fact that procuring entity has
to review documents describing the bid and other bidder documents.

Disqualification
~~~~~~~~~~~~~~~~

The protocol of Qualification Committee decision should be uploaded as
document into award and later its status should switch to either `active`
(if it is accepted) or `unsuccessful` (if rejected).

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/awards/{}/documents

The Qualification Comittee can upload several documents, like decisions to
prolong the qualification process to allow the bidder to collect all
necessary documents or correct errors.  Such documents would help to have
procedure as transparent as possible and will reduce risk of cancellation by
Complaint Review Body.

.. sourcecode:: http

  PATCH /tenders/64e93250be76435397e8c992ed4214d1/awards/{} HTTP/1.1

  {
      "data":{
          "awardStatus": "unsuccessful"
      }
  }

.. sourcecode:: http

  HTTP/1.1 200 OK
  Location: /tenders/64e93250be76435397e8c992ed4214d1/awards/ea36a10ad89649ccac253f23d8e0e80d HTTP/1.1

Note that after award rejection the next bid in the value-sorted bid
sequence becomes subject of subsequent award.  For convenience you can use
the `Location` response header from the response above that is pointing
award in "pending" state.


Contract Awarding
~~~~~~~~~~~~~~~~~

Protocol upload:

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/awards/{}/documents

Confirming the Award:

.. sourcecode:: http

  PATCH /tenders/64e93250be76435397e8c992ed4214d1/awards/{} HTTP/1.1

  {
      "data":{
          "awardStatus": "active"
      }
  }

.. sourcecode:: http

  HTTP/1.1 200 OK

The procuring entity can wait until bidder provides all missing documents
(licenses, certificates, statements, etc.) or update original bid documents
to correct errors.  Alternatively they can reject the bid if documents
provided does not satisfy the pass/fail criterias of tender (even before
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

Note that there is Location header returned that aid in locating the "fresh"
award that is most likely subject for disqualification:

.. include:: qualification/award-active-cancel-upload.http
   :code:

.. include:: qualification/award-active-cancel-disqualify.http
   :code:

In the case there is another Bid for qualification, there will be Location
header in the response poining its Award.


Influence of Complaint Satisfaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If decision of the procuring entity is considered unfair any bidder can file
complaint and after proper review the whole awarding process can start from
the award in question.  When Complaint Review Body satifies the complaint,
all awards registered in the system that were issued (including the one that
complaint was filed against) are cancelled (switch to `cancelled` status). 
New pending award is generated and Procuring Entity is obliged to qualify it
again, taking into consideration recommendations in the report of Complaint
Review Body.
