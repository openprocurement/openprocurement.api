.. Kicking page rebuild 2014-10-30 17:00:08
.. _bidding:

Bidder Operations
=================

Registration of Bid proposal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/bids/ HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/bids/4879d3f8ee2443169b5fbbc9f89fa607

Uploading Bid documents
~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  POST /tenders/64e93250be76435397e8c992ed4214d1/bids/4879d3f8ee2443169b5fbbc9f89fa607/documents HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 201 Created
  Location: /tenders/64e93250be76435397e8c992ed4214d1/bids/4879d3f8ee2443169b5fbbc9f89fa607/documents/bd2e4c64179445cab93987fff3d58d23


Update of proposal
~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  PATCH /tenders/64e93250be76435397e8c992ed4214d1/bids/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Updating Bid documents
~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  PUT /tenders/64e93250be76435397e8c992ed4214d1/bids/4879d3f8ee2443169b5fbbc9f89fa607/documents/bd2e4c64179445cab93987fff3d58d23 HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 200 Created

  {
      "data": {
          ...
          "id": "ddd45992f1c545b9b03302205962265b", 
          ...
          "url": ".../tenders/64e93250be76435397e8c992ed4214d1/bids/4879d3f8ee2443169b5fbbc9f89fa607/documents/bd2e4c64179445cab93987fff3d58d23?download=7d56370415484488bbb621b8cea6315b"
      }
  }
  
Cancelling the proposal
~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: http

  DELETE /tenders/64e93250be76435397e8c992ed4214d1/bids/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1

.. sourcecode:: http

  HTTP/1.1 200 OK

Bids Listing
~~~~~~~~~~~~

After auction ends it is possible to get full information about bids and bidders that submitted them:

.. sourcecode:: http

  GET /api/0/tenders/6f73bf0f7f734f459f7e37e3787054a0/bids HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=UTF-8

  {
      "data": [
          {
              "date": "2014-12-16T04:44:23.569815+02:00", 
              "documents": [
                  {
                      "dateModified": "2014-12-16T04:44:25.010930+02:00", 
                      "datePublished": "2014-12-16T04:44:25.010885+02:00", 
                      "format": "text/plain", 
                      "id": "ff001412c60c4164a0f57101e4eaf8aa", 
                      "title": "Proposal.pdf", 
                      "url": "https://public.api.openprocurement.org/api/0/tenders/6f73bf0f7f734f459f7e37e3787054a0/bids/f7fc1212f9f140bba5c4e3cd4f2b62d9/documents/ff001412c60c4164a0f57101e4eaf8aa?download=4f45bbd414104cd78faf620208efd824"
                  }
              ], 
              "id": "f7fc1212f9f140bba5c4e3cd4f2b62d9", 
              "tenderers": [
                  {
                      "address": {
                          "countryName": "Україна", 
                          "locality": "м. Вінниця", 
                          "postalCode": "21100", 
                          "region": "м. Вінниця", 
                          "streetAddress": "вул. Островського, 33"
                      }, 
                      "contactPoint": {
                          "email": "soleksuk@gmail.com", 
                          "name": "Сергій Олексюк", 
                          "telephone": "+380 (432) 21-69-30"
                      }, 
                      "identifier": {
                          "id": "13313462", 
                          "legalName": "Державне комунальне підприємство громадського харчування «Школяр»", 
                          "scheme": "UA-EDR", 
                          "uri": "http://sch10.edu.vn.ua/"
                      }, 
                      "name": "ДКП «Школяр»"
                  }
              ], 
              "value": {
                  "amount": 475000.0, 
                  "currency": "UAH", 
                  "valueAddedTaxIncluded": true
              }
          }, 
          {
              "date": "2014-12-16T04:44:26.973605+02:00", 
              "id": "25261352d2d042ff8639f65b68e95e9f", 
              "tenderers": [
                  {
                      "address": {
                          "countryName": "Україна", 
                          "locality": "м. Вінниця", 
                          "postalCode": "21018", 
                          "region": "м. Вінниця", 
                          "streetAddress": "вул. Юності, 30"
                      }, 
                      "contactPoint": {
                          "email": "alla.myhailova@i.ua", 
                          "name": "Алла Михайлова", 
                          "telephone": "+380 (432) 460-665"
                      }, 
                      "identifier": {
                          "id": "13306232", 
                          "legalName": "Державне комунальне підприємство громадського харчування «Меридіан»", 
                          "scheme": "UA-EDR", 
                          "uri": "http://sch10.edu.vn.ua/"
                      }, 
                      "name": "ДКП «Меридіан»"
                  }
              ], 
              "value": {
                  "amount": 480000.0, 
                  "currency": "UAH", 
                  "valueAddedTaxIncluded": true
              }
          }, 
          {
              "date": "2014-12-16T04:44:27.976478+02:00", 
              "id": "7ec725815ef448a9b857129024395638", 
              "tenderers": [
                  {
                      "address": {
                          "countryName": "Україна", 
                          "locality": "м. Вінниця", 
                          "postalCode": "21018", 
                          "region": "м. Вінниця", 
                          "streetAddress": "вул. Юності, 30"
                      }, 
                      "contactPoint": {
                          "email": "alla.myhailova@i.ua", 
                          "name": "Алла Михайлова", 
                          "telephone": "+380 (432) 460-665"
                      }, 
                      "identifier": {
                          "id": "13306232", 
                          "legalName": "Державне комунальне підприємство громадського харчування «Меридіан»", 
                          "scheme": "UA-EDR", 
                          "uri": "http://sch10.edu.vn.ua/"
                      }, 
                      "name": "ДКП «Меридіан2»"
                  }
              ], 
              "value": {
                  "amount": 482000.0, 
                  "currency": "UAH", 
                  "valueAddedTaxIncluded": true
              }
          }
      ]
  }


Retrieving the proposal
~~~~~~~~~~~~~~~~~~~~~~~

Individual bid can be retrieved via its `id`:

.. sourcecode:: http

  GET /api/0/tenders/6f73bf0f7f734f459f7e37e3787054a0/bids/f7fc1212f9f140bba5c4e3cd4f2b62d9 HTTP/1.1
 
.. sourcecode:: http

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=UTF-8

  {
      "data": {
          "date": "2014-12-16T04:44:23.569815+02:00", 
          "documents": [
              {
                  "dateModified": "2014-12-16T04:44:25.010930+02:00", 
                  "datePublished": "2014-12-16T04:44:25.010885+02:00", 
                  "format": "text/plain", 
                  "id": "ff001412c60c4164a0f57101e4eaf8aa", 
                  "title": "Proposal.pdf", 
                  "url": "https://public.api.openprocurement.org/api/0/tenders/6f73bf0f7f734f459f7e37e3787054a0/bids/f7fc1212f9f140bba5c4e3cd4f2b62d9/documents/ff001412c60c4164a0f57101e4eaf8aa?download=4f45bbd414104cd78faf620208efd824"
              }
          ], 
          "id": "f7fc1212f9f140bba5c4e3cd4f2b62d9", 
          "tenderers": [
              {
                  "address": {
                      "countryName": "Україна", 
                      "locality": "м. Вінниця", 
                      "postalCode": "21100", 
                      "region": "м. Вінниця", 
                      "streetAddress": "вул. Островського, 33"
                  }, 
                  "contactPoint": {
                      "email": "soleksuk@gmail.com", 
                      "name": "Сергій Олексюк", 
                      "telephone": "+380 (432) 21-69-30"
                  }, 
                  "identifier": {
                      "id": "13313462", 
                      "legalName": "Державне комунальне підприємство громадського харчування «Школяр»", 
                      "scheme": "UA-EDR", 
                      "uri": "http://sch10.edu.vn.ua/"
                  }, 
                  "name": "ДКП «Школяр»"
              }
          ], 
          "value": {
              "amount": 475000.0, 
              "currency": "UAH", 
              "valueAddedTaxIncluded": true
          }
      }
  }
