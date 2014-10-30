.. Kicking page rebuild 2014-10-30 17:00:08
.. _qualification:

Qualification Operations
========================

Contract Awarding
~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/awards HTTP/1.1

  {
      "data":{
          "awardStatus": "pending"
      }
  }

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/awards/ea36a10ad89649ccac253f23d8e0e80d HTTP/1.1

Disqualification
~~~~~~~~~~~~~~~~

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/awards HTTP/1.1

  {
      "data":{
          "awardStatus": "unsuccessful"
      }
  }

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/awards/ea36a10ad89649ccac253f23d8e0e80d HTTP/1.1
