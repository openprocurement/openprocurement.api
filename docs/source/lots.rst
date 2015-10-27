.. _lots:

Tenders with multiple Lots
==========================

When having tender with separate items that can be proveded by different
providers it is possible to split the tender into :ref:`Lots <lot>`.  Each
Lot has own budget (i.e. `Lot.value`).

Multilot Tender shares general documentation, and can have lot-specific and
even item-specific documentation.

The same applies to :ref:`Questions <question>` and answers. Question placed
in Tender can be general, lot-specific or item-specific.

When bidding provider can place bid against single lot, multiple lots or
even all lots of the tender.  Each of the documents attached to the
:ref:`Bid` can be general, lot-specific or item-specific.

Each Lot has has own auction and awarding process.

Each Lot can be cancelled individually, not affecting processes that take
place in other lots.

Announcing Multilot tender
--------------------------

One have to create Multilot tender into multiple steps. There should be
tender created (can have items).

Then all lots have to be added to Tender into separate requests.

Items should be distributed among the lots.

Bidding in Multilot tender
--------------------------

Bid should have `lotValues` property consisting of multiple :ref:`LotValue`
objects.  Each should reference lot the bid is placed against via
`relatedLot` property.

Auction participation URLs are available for each of the lots submited.

Qualification in Multilot tender
--------------------------------

After Auctions are over each active lot has own awarding process started.
I.e.  there are multiple award objects created in :ref:`Tender` each
requiring decision (disqualification or accept).

When all qualification processes end, and all stand still periods end, the
whole tender switch state to either `complete` or `unsuccessful` (if all
lots have theur awards `unsuccessful`).

