.. _meat:

Most economically advantageous tenders (MEAT)
=============================================

Besides simple price-only tenders it is possible to announce the tender
where other factors are valuable.  Such tenders define features that
procuring entity is interested in and how much different options influence
the decision about the winner.  Features can describe properties of
tenderer, lot or item(s) being procured. Each option offered has numerical
value that defines level of its importance compared to price.  Bidders are
doing self evaluation and provide the Parameters of their proposal (the
actual value of each feature) along with financial part of a bid.

For more information read `Non-price criteria <http://openprocurement.org/en/nonprice-criteria.html>`_.

The :ref:`Feature` is a data structure, part of the :ref:`Tender`. Tender can
have multiple features associated. Feature can be associated with tenderer,
lot or individual Item being procured. Features are identified with code,
which are unique within the tender.

.. sourcecode:: json

  [
        {
            "code":"ee3e24bc17234a41bd3e3a04cc28e9c6",
            "featureOf":"tenderer",
            "title":"Термін оплати",
            "description":"Умови відстрочки платежу після поставки товару",
            "enum":[
                {
                    "value":0.15,
                    "title":"180 днів та більше"
                },
                {
                    "value":0.1,
                    "title":"90-179 днів",
                },
                {
                    "value":0.05,
                    "title":"30-89 днів"
                },
                {
                    "value":0,
                    "title":"Менше 30 днів"
                }
            ]
        },
        {
            "code":"48cfd91612c04125ab406374d7cc8d93",
            "featureOf":"item",
            "relatedItem":"edd0032574bf4402877ad5f362df225a",
            "title":"Сорт",
            "description":"Сорт продукції",
            "enum":[
                {
                    "value":0.05,
                    "title":"Вищий"
                },
                {
                    "value":0.01,
                    "title":"Перший",
                },
                {
                    "value":0,
                    "title":"Другий"
                }
            ]
        }
  ]

:ref:`Parameters <parameter>` provided by :ref:`bidders <Bid>` should correspond to a set
of required features.  Parameters are linked to features using their codes.


.. sourcecode:: json

   [
            {
                "code":"ee3e24bc17234a41bd3e3a04cc28e9c6",
                "value":0.1
            },
            {
                "code":"48cfd91612c04125ab406374d7cc8d93",
                "value":0.05
            }
   ]

Announcing MEAT
---------------

Features can be set in :ref:`Tender` pretty the :ref:`same way <procuring>` as Items are - with
POST request.

.. sourcecode:: http

  POST /tenders HTTP/1.1

  {"data": {
    ...
    "features": [...],
    ...
  }

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1

Changing Features
~~~~~~~~~~~~~~~~~

In the case that Features should be changed one can send PATCH that replaces
Tender.features with new set:

.. sourcecode:: http

  PATCH /tenders HTTP/1.1

  {"data": {
    "features": [...]
  }

.. sourcecode:: http

  HTTP/1.1 200 OK

Removing Features
~~~~~~~~~~~~~~~~~

In case no Features are needed, they can be removed altogether with following request:

.. sourcecode:: http

  PATCH /tenders HTTP/1.1

  {"data": {
    "features": []
  }

.. sourcecode:: http

  HTTP/1.1 200 OK

Bidding in MEAT
---------------

The same applies to :ref:`Bid` - Parameters of a Bid can be set initially with POST
request and modified later with PATCH requests (see more at :ref:`bidding`).

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/bids HTTP/1.1

  {"data": {
    ...
    "parameters": [...],
    ...
  }

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/bid/4879d3f8ee2443169b5fbbc9f89fa607
 

Qualification in MEAT
---------------------

During auction Bidder can bid with his/her bid price and see normalized price of
his/her bid against normalized bids of other bidders.  Ranking in auction is
performed with normalized price where both price value and other
`Bid.parameters` are taken into consideration.
