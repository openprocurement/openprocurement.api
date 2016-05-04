.. _2pc:

2 Phase Commit
==============

Creating tender with 2 Phase Commit
-----------------------------------

Let's create tender in draft status:

.. include:: tutorial/tender-post-2pc.http
   :code:

And now switch to `active.enquiries` status:

.. include:: tutorial/tender-patch-2pc.http
   :code:
