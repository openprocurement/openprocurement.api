.. Kicking page rebuild 2014-10-30 17:00:08
.. _bidding:

Bidder Operations
=================

Registration of Bid proposal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: bidding/register-bidder.http
   :code:

Uploading Bid documents
~~~~~~~~~~~~~~~~~~~~~~~

.. include:: bidding/upload-bid-proposal.http
   :code:

Update of proposal
~~~~~~~~~~~~~~~~~~

.. include:: bidding/patch-bid.http
   :code:

Updating Bid documents
~~~~~~~~~~~~~~~~~~~~~~

.. include:: bidding/update-bid-document.http
   :code:

Cancelling the proposal
~~~~~~~~~~~~~~~~~~~~~~~

Deleted bid data is returned with answer from server.

.. include:: bidding/cancel-bid.http
   :code:

Bids Listing
~~~~~~~~~~~~

After auction ends it is possible to get full information about bids and bidders that submitted them:

.. include:: bidding/get-all-bids.http
   :code:

Retrieving the proposal
~~~~~~~~~~~~~~~~~~~~~~~

Individual bid can be retrieved via its `id`:

.. include:: bidding/get-bid-by-id.http
   :code:
