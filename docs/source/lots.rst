.. _lots:

Tenders with multiple Lots
==========================

When having tender with separate items that can be supplied by different
providers it is possible to split the tender into :ref:`Lots <lot>`.  Each
Lot has its own budget (i.e. `Lot.value`).

For more information read `Tender with multiple lots <http://openprocurement.org/en/multilots.html>`_.

.. sourcecode:: json

  {
    "lots": [
      {
        "id": "7d774fbf1e86420484c7d1a005cc283f",
        "title": "Lot #1: Kyiv stationey",
        "description": "Items for Kyiv office",
        "value": {"currency": "UAH", "amount": 8000.0, "valueAddedTaxIncluded": true},
        "minimalStep": {"currency": "UAH", "amount": 30.0, "valueAddedTaxIncluded": true},
        "status": "active"
      }, {
        "id": "563ef5d999f34d36a5a0e4e4d91d7be1",
        "title": "Lot #1: Lviv stationey",
        "description": "Items for Lviv office",
        "value": {"currency": "UAH", "amount": 9000.0, "valueAddedTaxIncluded": true},
        "minimalStep": {"currency": "UAH", "amount": 35.0, "valueAddedTaxIncluded": true},
        "status": "active"
      }
    ]
  }

Multilot Tender shares general documentation, and can have lot-specific and
even item-specific documentation.

.. sourcecode:: json

  {
    "documents": [
      {
        "format": "application/msword",
        "url": "...",
        "title": "kyiv-specs.doc",
        "datePublished": "2015-10-27T14:01:16.155803+02:00",
        "dateModified": "2015-10-27T14:01:16.155844+02:00",
        "id": "9491647572294c2bb20bf28f16d14dd8",
        "documentOf": "lot",
        "relateLot": "7d774fbf1e86420484c7d1a005cc283f"
      }
    ]
  }

The same applies to :ref:`Questions <question>` and answers. Question placed
in Tender can be general, lot-specific or item-specific.

When bidding, provider can place bid against single lot, multiple lots or
even all lots of the tender.

.. sourcecode:: json

  {
    "lotValues": [
      {
        "value": {"currency": "UAH", "amount": 7750.0, "valueAddedTaxIncluded": true},
        "reatedLot": "7d774fbf1e86420484c7d1a005cc283f",
        "date": "2015-11-01T12:43:12.482645+02:00"
      }, {
        "value": {"currency": "UAH", "amount": 8125.0, "valueAddedTaxIncluded": true},
        "reatedLot": "563ef5d999f34d36a5a0e4e4d91d7be1",
        "date": "2015-11-01T12:43:12.482645+02:00"
      }
    ],
    "..."
  }

Each of the :ref:`documents <document>` attached to the :ref:`Bid` can be
general, lot-specific or item-specific.

Each Lot has its own auction and awarding process.

Each Lot can be cancelled individually, not affecting processes that take
place in other lots.

Announcing Multilot tender
--------------------------

One has to create Multilot tender in several steps. There should be
tender created with items.

.. sourcecode:: http

  POST /tenders HTTP/1.1

  {"data": {
     "items":[
        {"description": "", ... },
        {"description": "", ... }
       ],
     ...
    }}

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1

  {"data": {
    "items":[
        {"id": "c25264295db0463ba533fd380756cff1", "description": "", ... },
        {"id": "f94aa51e2af944e08e02a4063121f93c", "description": "", ... }
      ],
    ...
    },
    ...
  }

Then all lots have to be added to Tender with separate requests.

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/lots HTTP/1.1

  {"data": {..}}

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/lots/7d774fbf1e86420484c7d1a005cc283f

2nd lot:

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/lots HTTP/1.1

  {"data": {..}}

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/lots/563ef5d999f34d36a5a0e4e4d91d7be1

Items should be distributed among the lots.

.. sourcecode:: http

  PATCH /tenders/64e93250be76435397e8c992ed4214d1 HTTP/1.1

  {"data": {
    "items":[
        {"id": "c25264295db0463ba533fd380756cff1", "relatedLot": "7d774fbf1e86420484c7d1a005cc283f"},
        {"id": "f94aa51e2af944e08e02a4063121f93c", "relatedLot": "563ef5d999f34d36a5a0e4e4d91d7be1"}
      ],
    ...
    },
    ...
  }

Bidding in Multilot tender
--------------------------

Bid should have `lotValues` property consisting of multiple :ref:`LotValue`
objects.  Each should reference lot the bid is placed against via
`relatedLot` property.

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/bids HTTP/1.1

  {"data": {
    "lotValues": [
      {
        "value": {"currency": "UAH", "amount": 7750.0, "valueAddedTaxIncluded": true},
        "reatedLot": "7d774fbf1e86420484c7d1a005cc283f",
        "date": "2015-11-01T12:43:12.482645+02:00"
      }, {
        "value": {"currency": "UAH", "amount": 8125.0, "valueAddedTaxIncluded": true},
        "reatedLot": "563ef5d999f34d36a5a0e4e4d91d7be1",
        "date": "2015-11-01T12:43:12.482645+02:00"
      }
    ],
    ...
  }}

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/bids/ae836da01ef749e494427dc591d36062

Auction participation URLs are available for each of the submitted lots.

Qualification in Multilot tender
--------------------------------

After Auctions are over each active lot has its own awarding process started.
I.e.  there are multiple award objects created in :ref:`Tender` each
requiring decision (disqualification or acceptance).

.. sourcecode:: http

  GET /tenders/64e93250be76435397e8c992ed4214d1/awards HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

  {"data": [
      {
          "status": "pending",
          "bid_id": "ae836da01ef749e494427dc591d36062",
          "value": {"currency": "UAH", "amount": 7750.0, "valueAddedTaxIncluded": true},
          "id": "c3179dd8609340a7ba9e5fe91762f564",
          "lotId": "7d774fbf1e86420484c7d1a005cc283f",
          "..."
      }, {
          "status": "pending",
          "bid_id": "ae836da01ef749e494427dc591d36062",
          "value": {"currency": "UAH", "amount": 8125.0, "valueAddedTaxIncluded": true},
          "id": "c99e30174b10418bac026a77d41288d7",
          "lotId": "563ef5d999f34d36a5a0e4e4d91d7be1",
          "..."
      }
    ]
  }


When all qualification processes end, and all stand still periods end, the
whole tender switch state to either `complete` or `unsuccessful` (if awads
for all lots are `unsuccessful`).

