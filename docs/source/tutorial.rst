.. _tutorial:

Tutorial
========

Let's try exploring the `/tenders` endpoint::

  curl -v http://api-sandbox.openprocurement.org/api/0/tenders
  > GET /api/0/tenders HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  >
  < HTTP/1.1 200 OK
  < Content-Type: application/json; charset=UTF-8
  < 
  {
    "data": []
  }

Just invoking it reveals empty set.

Now let's attempt creating some tender::

  curl -v -X POST http://api-sandbox.openprocurement.org/api/0/tenders
  > POST /api/0/tenders HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > 
  < HTTP/1.1 415 Unsupported Media Type
  < Content-Type: application/json; charset=UTF-8
  < 
  {
    "status": "error",
    "errors": [
      {
	"location": "header",
	"name": "Content-Type",
	"description": "Content-Type header should be one of ['application\/json']"
      }
    ]
  }

Error states that only accepted Content-Type is `application/json`.

Let's satisfy the Content-type requirement::

  curl -v -H "Content-Type: application/json" -X POST http://api-sandbox.openprocurement.org/api/0/tenders
  > POST /api/0/tenders HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > Content-Type: application/json
  > 
  < HTTP/1.1 422 Unprocessable Entity
  < Content-Type: application/json; charset=UTF-8
  < 
  {
    "status": "error",
    "errors": [
      {
	"location": "body",
	"name": "data",
	"description": "No JSON object could be decoded"
      }
    ]
  }

Error states that no `data` found in JSON body.

Let's provide the data attribute in the body submitted::

  curl -v -H "Content-Type: application/json" -X POST --data @data.json http://api-sandbox.openprocurement.org/api/0/tenders
  > POST /api/0/tenders HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > Content-Type: application/json
  > 
  > {
  >    "data":{}
  > }

  < HTTP/1.1 201 Created
  < Content-Type: application/json; charset=UTF-8
  < Location: http://api-sandbox.openprocurement.org/api/0/tenders/be40e257812044f3913534cc537d1f99
  < 
  {
    "data": {
      "id": "be40e257812044f3913534cc537d1f99",
      "tenderID": "UA-be40e257812044f3913534cc537d1f99",
      "modified": "2014-10-25T00:24:12.772078"
    }
  }

Success! Now we can see that new object was created. Response code is `201` and `Location` response header reports the location of object created. The body of response reveals the information about tender created, its internal `id` (that matches the `Location` segment), its official `tenderID` and `modified` datestamp stating the moment in time when tender was last modified.

Let's access the URL of object created (the `Location` header of the response)::

  curl -v http://api-sandbox.openprocurement.org/api/0/tenders/be40e257812044f3913534cc537d1f99
  > GET /api/0/tenders/be40e257812044f3913534cc537d1f99 HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > 
  < HTTP/1.1 200 OK
  < Content-Type: application/json; charset=UTF-8
  < 
  {
    "data": {
      "id": "be40e257812044f3913534cc537d1f99",
      "tenderID": "UA-be40e257812044f3913534cc537d1f99",
      "modified": "2014-10-25T00:24:12.772078"
    }
  }

We can see the same response we got after creating tender. 

Let's see what listing of tenders reveals us::

  curl -v http://api-sandbox.openprocurement.org/api/0/tenders/
  > GET /api/0/tenders/ HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > 
  < HTTP/1.1 200 OK
  < Content-Type: application/json; charset=UTF-8
  < 
  {
    "data": [
      {
	"id": "be40e257812044f3913534cc537d1f99",
	"modified": "2014-10-25T00:24:12.772078"
      }
    ]
  }

We do see the internal `id` of a tender (that can be used to construct full URL by prepending `http://api-sandbox.openprocurement.org/api/0/tenders/`) and its `modified` datestamp.

Let's try creating tender with more data, passing the `procuringEntity` of a tender::

  curl -v -H "Content-Type: application/json" --data @tender.json -X POST http://api-sandbox.openprocurement.org/api/0/tenders
  > POST /api/0/tenders HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > Content-Type: application/json
  > 
  > {
  >     "data":{
  >         "procuringEntity": {
  >             "id": {
  >                 "name": "Заклад \"Загальноосвітня школа І-ІІІ ступенів № 10 Вінницької міської ради\"",
  >                 "scheme": "https://ns.openprocurement.org/ua/edrpou",     
  >                 "uid": "21725150",
  >                 "uri": "http://sch10.edu.vn.ua/"
  >             },
  >             "address": {
  >                 "countryName": "Україна",
  >                 "postalCode": "21027",
  >                 "region": "м. Вінниця",
  >                 "locality": "м. Вінниця",
  >                 "streetAddress": "вул. Стахурського. 22"
  >             }
  >         }
  >     }
  > }

  < HTTP/1.1 201 Created
  < Content-Type: application/json; charset=UTF-8
  < Location: http://api-sandbox.openprocurement.org/api/0/tenders/8c2ba371505348ed8f5f0e5119a80451
  < 
  {
    "data": {
      "id": "8c2ba371505348ed8f5f0e5119a80451",
      "tenderID": "UA-8c2ba371505348ed8f5f0e5119a80451",
      "modified": "2014-10-25T00:37:13.847358",
      "procuringEntity": {
	"id": {
	  "scheme": "https:\/\/ns.openprocurement.org\/ua\/edrpou",
	  "name": "\u0417\u0430\u043a\u043b\u0430\u0434 \"\u0417\u0430\u0433\u0430\u043b\u044c\u043d\u043e\u043e\u0441\u0432\u0456\u0442\u043d\u044f \u0448\u043a\u043e\u043b\u0430 \u0406-\u0406\u0406\u0406 \u0441\u0442\u0443\u043f\u0435\u043d\u0456\u0432 \u2116 10 \u0412\u0456\u043d\u043d\u0438\u0446\u044c\u043a\u043e\u0457 \u043c\u0456\u0441\u044c\u043a\u043e\u0457 \u0440\u0430\u0434\u0438\"",
	  "uri": "http:\/\/sch10.edu.vn.ua\/",
	  "uid": "21725150"
	},
	"address": {
	  "postalCode": "21027",
	  "countryName": "\u0423\u043a\u0440\u0430\u0457\u043d\u0430",
	  "streetAddress": "\u0432\u0443\u043b. \u0421\u0442\u0430\u0445\u0443\u0440\u0441\u044c\u043a\u043e\u0433\u043e. 22",
	  "region": "\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f",
	  "locality": "\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f"
	}
      }
    }
  }

And again we have `201 Created` response code, `Location` header and body wth extra `id`, `tenderID`, and `modified` properties.

Let's check what tender registry contains::

  curl -v http://api-sandbox.openprocurement.org/api/0/tenders/
  > GET /api/0/tenders/ HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > 
  < HTTP/1.1 200 OK
  < Content-Type: application/json; charset=UTF-8
  <
  {
    "data": [
      {
	"id": "be40e257812044f3913534cc537d1f99",
	"modified": "2014-10-25T00:24:12.772078"
      },
      {
	"id": "8c2ba371505348ed8f5f0e5119a80451",
	"modified": "2014-10-25T00:37:13.847358"
      }
    ]
  }

And indeed we have 2 tenders now.

Let's update tender by providing it with all other essential properties::

  curl -v -H "Content-Type: application/json" -X PATCH --data @tender-update.json http://api-sandbox.openprocurement.org/api/0/tenders/8c2ba371505348ed8f5f0e5119a80451
  > PATCH /api/0/tenders/8c2ba371505348ed8f5f0e5119a80451 HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > Content-Type: application/json
  > 
  > {
  >     "data":{
  >         "totalValue": {
  >             "amount": 50000,
  >             "currency": "UAH",
  >             "valueAddedTaxIncluded": true
  >         },
  >         "itemsToBeProcured": [
  >             {
  >                 "description": "Послуги шкільних їдалень",
  >                 "primaryClassification": {
  >                     "scheme": "CPV",
  >                     "id": "55523100-3",
  >                     "description": "Послуги з харчування у школах"
  >                 },
  >                 "additionalClassification": [
  >                     {
  >                         "scheme": "ДКПП",
  >                         "id": "55.51.10.300",
  >                         "description": "Послуги шкільних їдалень"
  >                     }
  >                 ],   
  >                 "unitOfMeasure": "item",
  >                 "quantity": 5
  >             }
  >         ],   
  >         "clarificationPeriod": {
  >             "endDate": "2015-05-29T00:00:00"
  >         },
  >         "tenderPeriod": {
  >             "endDate": "2015-06-07T10:00:00"
  >         },
  >         "awardPeriod": {
  >             "endDate": "2015-06-18T00:00:00"
  >         }
  >     }
  > }

  < HTTP/1.1 200 OK
  < Content-Type: application/json; charset=UTF-8
  < 
  {
    "data": {
      "clarificationPeriod": {
	"startDate": null,
	"endDate": "2015-05-29T00:00:00.000000"
      },
      "awardPeriod": {
	"startDate": null,
	"endDate": "2015-06-18T00:00:00.000000"
      },
      "tenderPeriod": {
	"startDate": null,
	"endDate": "2015-06-07T10:00:00.000000"
      },
      "modified": "2014-10-25T00:42:44.968106",
      "itemsToBeProcured": [
	{
	  "unitOfMeasure": "item",
	  "description": "\u041f\u043e\u0441\u043b\u0443\u0433\u0438 \u0448\u043a\u0456\u043b\u044c\u043d\u0438\u0445 \u0457\u0434\u0430\u043b\u0435\u043d\u044c",
	  "valuePerUnit": null,
	  "additionalClassification": [
	    {
	      "scheme": "\u0414\u041a\u041f\u041f",
	      "id": "55.51.10.300",
	      "uri": null,
	      "description": "\u041f\u043e\u0441\u043b\u0443\u0433\u0438 \u0448\u043a\u0456\u043b\u044c\u043d\u0438\u0445 \u0457\u0434\u0430\u043b\u0435\u043d\u044c"
	    }
	  ],
	  "primaryClassification": {
	    "scheme": "CPV",
	    "id": "55523100-3",
	    "uri": null,
	    "description": "\u041f\u043e\u0441\u043b\u0443\u0433\u0438 \u0437 \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \u0443 \u0448\u043a\u043e\u043b\u0430\u0445"
	  },
	  "quantity": 5
	}
      ],
      "tenderID": "UA-8c2ba371505348ed8f5f0e5119a80451",
      "totalValue": {
	"currency": "UAH",
	"amount": 50000,
	"valueAddedTaxIncluded": true
      },
      "id": "8c2ba371505348ed8f5f0e5119a80451",
      "procuringEntity": {
	"id": {
	  "scheme": "https:\/\/ns.openprocurement.org\/ua\/edrpou",
	  "name": "\u0417\u0430\u043a\u043b\u0430\u0434 \"\u0417\u0430\u0433\u0430\u043b\u044c\u043d\u043e\u043e\u0441\u0432\u0456\u0442\u043d\u044f \u0448\u043a\u043e\u043b\u0430 \u0406-\u0406\u0406\u0406 \u0441\u0442\u0443\u043f\u0435\u043d\u0456\u0432 \u2116 10 \u0412\u0456\u043d\u043d\u0438\u0446\u044c\u043a\u043e\u0457 \u043c\u0456\u0441\u044c\u043a\u043e\u0457 \u0440\u0430\u0434\u0438\"",
	  "uri": "http:\/\/sch10.edu.vn.ua\/",
	  "uid": "21725150"
	},
	"address": {
	  "postalCode": "21027",
	  "countryName": "\u0423\u043a\u0440\u0430\u0457\u043d\u0430",
	  "streetAddress": "\u0432\u0443\u043b. \u0421\u0442\u0430\u0445\u0443\u0440\u0441\u044c\u043a\u043e\u0433\u043e. 22",
	  "region": "\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f",
	  "locality": "\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f"
	}
      }
    }
  }

We see the added properies merged with existing data of tender. Additionally the `modified` property updated to reflect the last modification datestamp.

Checking the listing again reflets the new modification date::

  curl -v http://api-sandbox.openprocurement.org/api/0/tenders/
  > GET /api/0/tenders/ HTTP/1.1
  > Host: api-sandbox.openprocurement.org
  > 
  < HTTP/1.1 200 OK
  < Content-Type: application/json; charset=UTF-8
  <
  {
    "data": [
      {
	"modified": "2014-10-25T00:42:44.968106",
	"id": "8c2ba371505348ed8f5f0e5119a80451"
      },
      {
	"id": "be40e257812044f3913534cc537d1f99",
	"modified": "2014-10-25T00:24:12.772078"
      }
    ]
  }

