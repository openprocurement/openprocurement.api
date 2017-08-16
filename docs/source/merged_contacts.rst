.. _merged_contracts:


Merge contracts
===============

For merge contracts `suppliers` must be the same. Let's get contracts.

.. include:: merged_contracts/all_pending_contracts.http
   :code:


Let's merge second contract in the first, for merging  the field `additionalAwardIDs` needs to be sent with list of merge awards id.
In response we must see `additionalAwardIDs`.

.. include:: merged_contracts/merge_contracts.http
   :code:

Now additional award must have a status `merged`, and field `mergedInto`. We can't make changes in additional contracts.

.. include:: merged_contracts/additional_contract.http
   :code:

Sign main contract
------------------

Set contract value and sign.

.. include:: merged_contracts/tender-contract-sign.http
   :code:

Cancel main award
-----------------

Let`s cancel award which contract has additional awards.

.. include:: merged_contracts/cancel_main_contract.http
   :code:

Lets look on contracts

.. include:: merged_contracts/contract_after_cancel_main_award.http
   :code:

We see that contract and award move in status `cancelled` and each additional contract has changed a status from `merged` to `pending`, and has removed a field `mergeInto`.


Cancel additional award
-----------------------

If additional award is canceled, then award and contract will move in status `cancelled`, and ID of award will be deleted from `additionalAwards` in the main contract

.. include:: merged_contracts/cancel_additional_contract.http
   :code:

Let's look on the main contract

.. include:: merged_contracts/main_contract_after_cancel_additional.http
   :code: