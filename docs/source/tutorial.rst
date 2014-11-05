.. _tutorial:

Tutorial
========

Let's try exploring the `/tenders` endpoint:

.. include:: tutorial/initial-tender-listing.http
   :code:

Just invoking it reveals empty set.

Now let's attempt creating some tender:

.. include:: tutorial/tender-post-attempt.http
   :code:

Error states that only accepted Content-Type is `application/json`.

Let's satisfy the Content-type requirement:

.. include:: tutorial/tender-post-attempt-json.http
   :code:

Error states that no `data` found in JSON body.

Let's provide the data attribute in the body submitted:

.. include:: tutorial/tender-post-attempt-json-data.http
   :code:

Success! Now we can see that new object was created. Response code is `201` and `Location` response header reports the location of object created. The body of response reveals the information about tender created, its internal `id` (that matches the `Location` segment), its official `tenderID` and `modified` datestamp stating the moment in time when tender was last modified.

Let's access the URL of object created (the `Location` header of the response):

.. include:: tutorial/blank-tender-view.http
   :code:

.. XXX body is empty for some reason (printf fails)

We can see the same response we got after creating tender. 

Let's see what listing of tenders reveals us:

.. include:: tutorial/tender-listing.http
   :code:

We do see the internal `id` of a tender (that can be used to construct full URL by prepending `http://api-sandbox.openprocurement.org/api/0/tenders/`) and its `modified` datestamp.

Let's try creating tender with more data, passing the `procuringEntity` of a tender:

.. include:: tutorial/create-tender-procuringEntity.http
   :code:

And again we have `201 Created` response code, `Location` header and body wth extra `id`, `tenderID`, and `modified` properties.

Let's check what tender registry contains:

.. include:: tutorial/tender-listing-after-procuringEntity.http
   :code:

And indeed we have 2 tenders now.

Let's update tender by providing it with all other essential properties:

.. include:: tutorial/patch-items-value-periods.http
   :code:

.. XXX body is empty for some reason (printf fails)

We see the added properies merged with existing data of tender. Additionally the `modified` property updated to reflect the last modification datestamp.

Checking the listing again reflects the new modification date:

.. include:: tutorial/tender-listing-after-patch.http
   :code:
