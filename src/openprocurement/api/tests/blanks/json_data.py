# -*- coding: utf-8 -*-
from copy import deepcopy

test_organization = {
    "name": u"Державне управління справами",
    "identifier": {
        "scheme": u"UA-EDR",
        "id": u"00037256",
        "uri": u"http://www.dus.gov.ua/"
    },
    "address": {
        "countryName": u"Україна",
        "postalCode": u"01220",
        "region": u"м. Київ",
        "locality": u"м. Київ",
        "streetAddress": u"вул. Банкова, 11, корпус 1"
    },
    "contactPoint": {
        "name": u"Державне управління справами",
        "telephone": u"0440000000"
    }
}

test_organization_loki = {
    "identifier": {
        "scheme": u"UA-EDR",
        "id": u"00037256",
    },
    "address": {
        "countryName": u"Україна",
    },
    "contactPoint": {
        "name": u"Державне управління справами",
        "telephone": u"0440000000"
    },
    'additionalContactPoints': [
        {'name': 'name', 'email': 'some@mail.com'}
    ]
}

test_document_data = {
    # 'url': self.generate_docservice_url(),
    'title': u'укр.doc',
    'hash': 'md5:' + '0' * 32,
    'format': 'application/msword'
}

test_item_data = {
    "id": u"0",
    "description": u"футляри до державних нагород",
    "classification": {
        "scheme": u"CAV",
        "id": u"39513200-3",
        "description": u"Cartons"
    },
    "additionalClassifications": [
        {
            "scheme": u"ДКПП",
            "id": u"17.21.1",
            "description": u"папір і картон гофровані, паперова й картонна тара"
        }
    ],
    "unit": {
        "name": u"item",
        "code": u"44617100-9"
    },
    "quantity": 5,
    "address": {
        "countryName": u"Україна",
        "postalCode": "79000",
        "region": u"м. Київ",
        "locality": u"м. Київ",
        "streetAddress": u"вул. Банкова 1"
    }
}

schema_properties = {
        u"code": "04000000-8",
        u"version": "001",
        u"properties": {
          u"totalArea": 200,
          u"year": 1998,
          u"floor": 3
        }
    }

schema_properties_341 = {
        u"code": "34100000-8",
        u"version": "001",
        u"properties": {
          u"make": u"Таврія",
          u"model": u"Славута",
          u"fuelType": ["petrol"]
        }
    }

schema_properties_060 = {
        u"code": "06000000-2",
        u"version": "002",
        "properties": {
          u"area": 1.2,
          u"cadastralNumber": "1234567890:12:123:1234",
          u"inUse": True
        }
    }

test_item_data_with_schema = deepcopy(test_item_data)
test_item_data_with_schema['classification']['id'] = schema_properties['code']
test_item_data_with_schema['schema_properties'] = schema_properties

test_item_data_with_schema_341 = deepcopy(test_item_data)
test_item_data_with_schema_341['classification']['id'] = schema_properties_341['code']
test_item_data_with_schema_341['schema_properties'] = schema_properties_341

test_item_data_with_schema_060 = deepcopy(test_item_data)
test_item_data_with_schema_060['classification']['id'] = schema_properties_060['code']
test_item_data_with_schema_060['schema_properties'] = schema_properties_060

test_asset_basic_data = {
    "title": u"Земля для космодрому",
    "assetType": "basic",
    "assetCustodian": deepcopy(test_organization),
    "classification": {
        "scheme": u"CAV",
        "id": u"39513200-3",
        "description": u"Земельні ділянки"
    },
    "unit": {
        "name": u"item",
        "code": u"39513200-3"
    },
    "quantity": 5,
    "address": {
        "countryName": u"Україна",
        "postalCode": "79000",
        "region": u"м. Київ",
        "locality": u"м. Київ",
        "streetAddress": u"вул. Банкова 1"
    },
    "value": {
        "amount": 100,
        "currency": u"UAH"
    }
}

test_asset_basic_data_with_schema = deepcopy(test_asset_basic_data)
test_asset_basic_data_with_schema['classification']['id'] = schema_properties['code']
test_asset_basic_data_with_schema['schema_properties'] = schema_properties

test_asset_basic_data_with_schema_341 = deepcopy(test_asset_basic_data)
test_asset_basic_data_with_schema_341['classification']['id'] = schema_properties_341['code']
test_asset_basic_data_with_schema_341['schema_properties'] = schema_properties_341

test_asset_basic_data_with_schema_060 = deepcopy(test_asset_basic_data)
test_asset_basic_data_with_schema_060['classification']['id'] = schema_properties_060['code']
test_asset_basic_data_with_schema_060['schema_properties'] = schema_properties_060

test_debt_data = {
    "agreementNumber": u"42",
    "debtorType": u"legalPerson",
    "dateSigned": u"2017-08-16T12:30:17.615196+03:00",
    "value": {
        "amount": 1,
        "currency": u"UAH"
    },
    "debtCurrencyValue": {
        "amount": 100,
        "currency": u"USD"
    },
}

test_asset_compound_data = deepcopy(test_asset_basic_data)
test_asset_compound_data['assetType'] = 'compound'
test_asset_compound_data['items'] = [test_item_data_with_schema, test_item_data_with_schema]

test_asset_compound_data_341 = deepcopy(test_asset_basic_data)
test_asset_compound_data_341['assetType'] = 'compound'
test_asset_compound_data_341['items'] = [test_item_data_with_schema_341, test_item_data_with_schema_341]

test_asset_compound_data_060 = deepcopy(test_asset_basic_data)
test_asset_compound_data_060['assetType'] = 'compound'
test_asset_compound_data_060['items'] = [test_item_data_with_schema_060, test_item_data_with_schema_060]

test_asset_claimrights_data = deepcopy(test_asset_compound_data)
test_asset_claimrights_data['assetType'] = 'claimRights'
test_asset_claimrights_data['debt'] = test_debt_data


test_lot_data = {
    "title": u"Тестовий лот",
    "description": u"Щось там тестове",
    "lotIdentifier": u"Q81318b19827",
    "lotType": "basic",
    "lotCustodian": deepcopy(test_organization),
    "assets": []
}

test_loki_item_data = deepcopy(test_item_data)
test_loki_item_data['registrationDetails'] = {
    'status': 'unknown'
}
test_loki_item_data.update(
    {
        "unit": {"code": "code"},
        "classification": {
            "scheme": "CAV-PS",
            "id": "06121000-6",
            "description": "Description"
        },
        "address": {"countryName": "Ukraine"},
        "quantity": 5.0001,
        "additionalClassifications": [
            {
                "scheme": u"UA-EDR",
                "id": u"17.21.1",
                "description": u"папір і картон гофровані, паперова й картонна тара"
            }
        ],
    }
)
