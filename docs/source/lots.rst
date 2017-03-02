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

.. include:: lots/tender-with-items-post-attempt-json-data.http
   :code:

Then all lots have to be added to Tender with separate requests.

.. include:: lots/first-lot-post-attempt.http
   :code:

2nd lot:

.. include:: lots/second-lot-post-attempt.http
   :code:

3nd lot:

.. include:: lots/third-lot-post-attempt.http
   :code:

Items should be distributed among the lots:

.. include:: lots/bound-lots-with-items.http
   :code:

Editing Lots
--------------------------

Lots can be edited, using Patch request. Changing second Lot's value:

.. include:: lots/patch-second-lot.http
   :code:

Lot can be cancelled:

.. include:: lots/cancel-third-lot.http
   :code:

Change the Items distribution among the lots:

.. include:: lots/second-bound-lots-with-items.http
   :code:

Bidding in Multilot tender
--------------------------

Bid should have `lotValues` property consisting of multiple :ref:`LotValue`
objects.  Each should reference lot the bid is placed against via
`relatedLot` property.

Register Bid for all active lots:

.. include:: lots/register-bidder-with-lot-values.http
   :code:

Register Bid only for second lot:

.. include:: lots/register-second-bidder-with-lot-values.http
   :code:

Auction participation URLs are available for each of the submitted lots.

Qualification in Multilot tender
--------------------------------

After Auctions are over each active lot has its own awarding process started.
I.e.  there are multiple award objects created in :ref:`Tender` each
requiring decision (disqualification or acceptance).

.. include:: lots/get-awards.http
   :code:

Confirming the Award for first Lot:

.. include:: lots/confirm-award-for-first-lot.http
   :code:

Cancel the Award for second Lot:

.. include:: lots/unsuccessful-award-for-second-lot.http
   :code:

Confirming the next pending Award for second Lot:

.. include:: lots/confirm-next-award-for-second-lot.http
   :code:

When all qualification processes end, and all stand still periods end, the
whole tender switch state to either `complete` or `unsuccessful` (if awads
for all lots are `unsuccessful`).
