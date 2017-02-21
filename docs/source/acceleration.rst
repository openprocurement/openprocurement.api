.. _acceleration:

Acceleration mode for sandbox
=============================

Acceleration mode was developed to enable procedures' testing in the sandbox and to reduce time frames of these procedures. 

**This mode will work only in the sandbox**.

To enable acceleration mode you will need to:

    * add additional parameter `mode` with a value ``test``;
    * set ``quick, accelerator=1440`` as text value for `procurementMethodDetails`. This parameter will accelerate auction periods. The number 1440 shows that restrictions and time frames will be reduced in 1440 times.
    * set ``quick`` as a value for `submissionMethodDetails`. This parameter works only with ``mode = "test"`` and will speed up auction start date.


Additional options
------------------

**no-auction option**

To enable this option: set ``quick(mode:no-auction)`` as a value for `submissionMethodDetails`.

``no-auction`` option allows conducting tender excluding auction stage. This means that `active.auction` stage will be completed based on the primary bid proposals; `auctionURL` will not be created, so auction can not be viewed.

**fast-forward option**

To enable this option: set ``quick(mode:fast-forward)`` as a value for `submissionMethodDetails`.

``fast-forward`` option allows skipping auction stage. This means that `active.auction` stage will be completed based on the primary bid proposals; although `auctionURL` will be created and auction can be viewed.
