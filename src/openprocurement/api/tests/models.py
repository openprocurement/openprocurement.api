# -*- coding: utf-8 -*-
import unittest
import os
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal

import mock
from isodate.duration import Duration
from libnacl.sign import Signer, Verifier
from schematics.exceptions import ConversionError, ValidationError, ModelValidationError
from schematics.types import BaseType

from openprocurement.api.config import (
    AppMetaSchema,
    AuctionModule,
    DefaultWriter,
    Config,
    User,
    Auth,
    Main,
    DB,
    DS,
)
from openprocurement.api.constants import LOKI_ITEM_CLASSIFICATION
from openprocurement.api.models.auction_models import (
    Document as AuctionDocument
)
from openprocurement.api.models.common import (
    Period,
    PeriodEndRequired,
    ContactPoint,
    Classification,
    Address,
    Location
)
from openprocurement.api.models.ocds import (
    Organization,
    Identifier,
    BaseItem,
    Unit,
    Value,
    ItemClassification,
    BaseDocument,
)
from openprocurement.api.models.registry_models import (
    RegistrationDetails,
    LokiItem,
    Decision,
    LokiDocument,
    AssetCustodian,
    AssetHolder
)
from openprocurement.api.models.roles import blacklist
from openprocurement.api.models.schematics_extender import (
    IsoDateTimeType, HashType, IsoDurationType, DecimalType
)
from openprocurement.api.tests.base import test_config_data, test_user_data
from openprocurement.api.tests.blanks.json_data import (
    test_item_data_with_schema,
    test_loki_item_data
)
from openprocurement.api.utils import get_now

now = get_now()


class SchematicsExtenderTest(unittest.TestCase):

    def test_IsoDateTimeType_model(self):

        dt = IsoDateTimeType()

        value = dt.to_primitive(now)
        self.assertEqual(now, dt.to_native(now))
        self.assertEqual(now, dt.to_native(value))

        date = datetime.now()
        value = dt.to_primitive(date)
        self.assertEqual(date, dt.to_native(date))
        self.assertEqual(now.tzinfo, dt.to_native(value).tzinfo)

        # ParseError
        for date in (None, '', 2017, "2007-06-23X06:40:34.00Z"):
            with self.assertRaisesRegexp(ConversionError, 
                      u'Could not parse %s. Should be ISO8601.' % date):
                dt.to_native(date)
        # OverflowError
        for date in (datetime.max, datetime.min):
            self.assertEqual(date, dt.to_native(date))
            with self.assertRaises(ConversionError):
                dt.to_native(dt.to_primitive(date))

    def test_DecimalType_model(self):
        number = '5.001'

        dt = DecimalType()

        value = dt.to_primitive(number)
        self.assertEqual(Decimal(number), dt.to_native(number))
        self.assertEqual(Decimal(number), dt.to_native(value))

        for number in (None, '5,5'):
            with self.assertRaisesRegexp(ConversionError, dt.messages['number_coerce'].format(number)):
                dt.to_native(number)

        dt = DecimalType(precision=-3, min_value=Decimal('0'), max_value=Decimal('10.0'))

        self.assertEqual(Decimal('0.111'), dt.to_native('0.11111'))
        self.assertEqual(Decimal('0.556'), dt.to_native('0.55555'))

        number = '-1.1'
        dt = DecimalType(min_value=0)
        with self.assertRaisesRegexp(ConversionError, dt.messages['number_min'].format(number)):
            dt.to_native(dt.to_primitive(number))

        number = '11.1'
        dt = DecimalType(max_value=0)
        with self.assertRaisesRegexp(ConversionError, dt.messages['number_max'].format(number)):
            dt.to_native(dt.to_primitive(number))

    def test_HashType_model(self):
        from uuid import uuid4

        hash = HashType()

        for invalid_hash in ['test', ':', 'test:']:
            with self.assertRaisesRegexp(ValidationError, "Hash type is not supported."):
                hash.to_native(invalid_hash)

        with self.assertRaisesRegexp(ValidationError, "Hash value is wrong length."):
            hash.to_native('sha512:')

        with self.assertRaisesRegexp(ConversionError, "Hash value is not hexadecimal."):
            hash.to_native('md5:{}'.format('-' * 32))

        result = 'md5:{}'.format(uuid4().hex)
        self.assertEqual(hash.to_native(result), result)

    def test_IsoDuration_model(self):
        dt = IsoDurationType()

        duration = Duration(days=5, hours=6)
        value = dt.to_primitive(duration)
        self.assertEqual(duration, dt.to_native(duration))
        self.assertEqual(duration, dt.to_native(value))

        duration_string = "P1DT12H"
        self.assertEqual(Duration(days=1, hours=12), dt.to_native(duration_string))
        self.assertEqual("P1DT12H", dt.to_primitive(Duration(days=1, hours=12)))

        duration_string = "P3Y1DT12H"
        self.assertEqual(Duration(years=3, days=1, hours=12), dt.to_native(duration_string))
        self.assertEqual("P3Y1DT12H", dt.to_primitive(Duration(years=3 ,days=1, hours=12)))

        # Iso8601Error
        for duration in (None, '', 2017, "X1DT12H"):
            with self.assertRaisesRegexp(ConversionError,
                      u'Could not parse %s. Should be ISO8601 duration format.' % duration):
                dt.to_native(duration)
        # OverflowError
        # for date in (Duration(12), datetime.min):
        #     self.assertEqual(date, dt.to_native(date))
        #     with self.assertRaises(ConversionError):
        #         dt.to_native(dt.to_primitive(date))


class DummyOCDSModelsTest(unittest.TestCase):
    """ Test Case for testing openprocurement.api.registry_models'
            - roles
            - serialization
            - validation
    """
    def test_Period_model(self):
        period = Period()

        self.assertEqual(period.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'Period Model has no role "test"'):
            period.serialize('test')

        data = {'startDate': now.isoformat()}
        period.import_data(data)
        period.validate()
        self.assertEqual(period.serialize(), data)
        data['endDate'] = now.isoformat()
        period.import_data(data)
        period.validate()
        self.assertEqual(period.serialize(), data)
        period.startDate += timedelta(3)
        with self.assertRaises(ModelValidationError) as ex:
            period.validate()
        self.assertEqual(ex.exception.messages,
                         {"startDate": ["period should begin before its end"]})

    def test_PeriodEndRequired_model(self):
        period = PeriodEndRequired()

        self.assertEqual(period.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'PeriodEndRequired Model has no role "test"'):
            period.serialize('test')

        period.endDate = now
        period.validate()

        period.startDate = now + timedelta(1)
        with self.assertRaises(ModelValidationError) as ex:
            period.validate()
        self.assertEqual(ex.exception.message,
                         {"startDate": ["period should begin before its end"]})

        period.endDate = None
        with self.assertRaises(ModelValidationError) as ex:
            period.validate()
        self.assertEqual(ex.exception.message,
                         {'endDate': [u'This field is required.']})

        period.endDate = now + timedelta(2)
        period.validate()

    def test_Value_model(self):
        value = Value()

        self.assertEqual(value.serialize().keys(),
                         ['currency', 'valueAddedTaxIncluded'])
        with self.assertRaisesRegexp(ValueError, 'Value Model has no role "test"'):
            value.serialize('test')

        self.assertEqual(Value.get_mock_object().serialize().keys(),
                         ['currency', 'amount', 'valueAddedTaxIncluded'])
        with self.assertRaises(ModelValidationError) as ex:
            value.validate()
        self.assertEqual(ex.exception.message,
                         {'amount': [u'This field is required.']})

        value.amount = -10
        self.assertEqual(value.serialize(), {'currency': u'UAH', 'amount': -10,
                                            'valueAddedTaxIncluded': True})
        with self.assertRaises(ModelValidationError) as ex:
            value.validate()
        self.assertEqual(ex.exception.message,
                         {'amount': [u'Float value should be greater than 0.']})
        self.assertEqual(value.to_patch(), value.serialize())

        value.amount = None
        with self.assertRaises(ModelValidationError) as ex:
            value.validate()
        self.assertEqual(ex.exception.message,
                         {"amount": ["This field is required."]})

        value.amount = .0
        value.currency = None
        self.assertEqual(value.serialize(), {'amount': 0.0, 'valueAddedTaxIncluded': True})
        value.validate()
        self.assertEqual(value.serialize(), {'amount': 0.0, 'valueAddedTaxIncluded': True, "currency": u"UAH"})

    def test_Unit_model(self):

        data = {'name': u'item', 'code': u'39513200-3'}

        unit = Unit(data)
        unit.validate()

        self.assertEqual(unit.serialize().keys(), ['code', 'name'])
        with self.assertRaisesRegexp(ValueError, 'Unit Model has no role "test"'):
            unit.serialize('test')

        unit.code = None
        with self.assertRaises(ModelValidationError) as ex:
            unit.validate()
        self.assertEqual(ex.exception.message,
                         {'code': [u'This field is required.']})

        data['value'] = {'amount': 5}
        unit = Unit(data)
        self.assertEqual(unit.serialize(), {'code': u'39513200-3', 'name': u'item',
                                            'value': {'currency': u'UAH', 'amount': 5., 'valueAddedTaxIncluded': True}})

        unit.value.amount = -1000
        unit.value.valueAddedTaxIncluded = False
        self.assertEqual(unit.serialize(), {'code': u'39513200-3', 'name': u'item',
                                            'value': {'currency': u'UAH', 'amount': -1000, 'valueAddedTaxIncluded': False}})
        with self.assertRaises(ModelValidationError) as ex:
            unit.validate()
        self.assertEqual(ex.exception.message,
                         {'value': {'amount': [u'Float value should be greater than 0.']}})

    def test_Classification_model(self):

        data = {'scheme': u'CAV', 'id': u'39513200-3', 'description': u'Cartons'}

        classification = Classification(data)
        classification.validate()

        self.assertEqual(classification.serialize(), data)
        with self.assertRaisesRegexp(ValueError, 'Classification Model has no role "test"'):
            classification.serialize('test')

        classification.scheme = None
        self.assertNotEqual(classification.serialize(), data)
        with self.assertRaises(ModelValidationError) as ex:
            classification.validate()
        self.assertEqual(ex.exception.message,
                         {"scheme": ["This field is required."]})

        scheme = data.pop('scheme')
        self.assertEqual(classification.serialize(), data)
        classification.scheme = scheme
        data["scheme"] = scheme
        classification.validate()

    @mock.patch.dict('openprocurement.api.constants.ITEM_CLASSIFICATIONS', {'CAV': ['test']})
    def test_ItemClassification_model(self):
        item_classification = ItemClassification.get_mock_object()

        self.assertIn('id', item_classification.serialize())
        with self.assertRaisesRegexp(ValueError, 'ItemClassification Model has no role "test"'):
            item_classification.serialize('test')

        item_classification.scheme = 'CAV'
        with self.assertRaises(ModelValidationError) as ex:
            item_classification.validate()
        self.assertEqual(ex.exception.message,
                         {"id": ["Value must be one of ['test']."]})

        item_classification.import_data({'scheme': 'CAV', 'id': 'test'})
        item_classification.validate()


    def test_Location_model(self):
        location = Location()

        self.assertEqual(location.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'Location Model has no role "test"'):
            location.serialize('test')

        with self.assertRaises(ModelValidationError) as ex:
            location.validate()
        self.assertEqual(ex.exception.messages, {'latitude': [u'This field is required.'],
                                        'longitude': [u'This field is required.']})
        location.import_data({'latitude': '123.1234567890',
                              'longitude': '-123.1234567890'})
        self.assertDictEqual(location.serialize(), {'latitude': '123.1234567890',
                                                    'longitude': '-123.1234567890'})
        location.validate()

    def test_Item_model(self):

        item = BaseItem(test_item_data_with_schema)
        item.validate()
        self.assertEqual(item.serialize()['schema_properties']['properties'], test_item_data_with_schema['schema_properties']['properties'])
        self.assertEqual(item.serialize()['schema_properties']['code'][0:2], test_item_data_with_schema['schema_properties']['code'][:2])
        self.assertEqual(item.serialize()['description'], test_item_data_with_schema['description'])
        self.assertEqual(item.serialize()['classification'], test_item_data_with_schema['classification'])
        self.assertEqual(item.serialize()['additionalClassifications'], test_item_data_with_schema['additionalClassifications'])
        self.assertEqual(item.serialize()['address'], test_item_data_with_schema['address'])
        self.assertEqual(item.serialize()['id'], test_item_data_with_schema['id'])
        self.assertEqual(item.serialize()['unit'], test_item_data_with_schema['unit'])
        self.assertEqual(item.serialize()['quantity'], test_item_data_with_schema['quantity'])

        with self.assertRaisesRegexp(ValueError, 'Item Model has no role "test"'):
            item.serialize('test')

        test_item_data_with_schema['location'] = {'latitude': '123', 'longitude': '567'}
        item2 = BaseItem(test_item_data_with_schema)
        item2.validate()

        self.assertNotEqual(item, item2)
        item2.location = None
        self.assertEqual(item, item2)

        with mock.patch.dict('openprocurement.api.models.ocds.BaseItem._options.roles', {'test': blacklist('__parent__', 'address')}):
            self.assertNotIn('address', item.serialize('test'))
            self.assertNotEqual(item.serialize('test'), item.serialize())
            self.assertEqual(item.serialize('test'), item2.serialize('test'))

    def test_Address_model(self):

        data = {
            "countryName": u"Україна",
            "postalCode": "79000",
            "region": u"м. Київ",
            "locality": u"м. Київ",
            "streetAddress": u"вул. Банкова 1"
        }

        address = Address(data)
        address.validate()

        self.assertEqual(address.serialize(), data)
        with self.assertRaisesRegexp(ValueError, 'Address Model has no role "test"'):
            address.serialize('test')

        address.countryName = None
        with self.assertRaises(ModelValidationError) as ex:
            address.validate()
        self.assertEqual(ex.exception.messages, {'countryName': [u'This field is required.']})
        address.countryName = data["countryName"]
        address.validate()
        self.assertEqual(address.serialize(), data)

    def test_Identifier_model(self):
        identifier = Identifier.get_mock_object()

        with self.assertRaisesRegexp(ValueError, 'Identifier Model has no role "test"'):
            identifier.serialize('test')

        with self.assertRaises(ModelValidationError) as ex:
            identifier.validate()
        self.assertEqual(ex.exception.messages, {"id": ["This field is required."]})

        identifier.id = 'test'
        identifier.validate()

        with mock.patch.dict('openprocurement.api.models.ocds.Identifier._options.roles', {'test': blacklist('id')}):
            self.assertIn('id', identifier.serialize().keys())
            self.assertNotIn('id', identifier.serialize('test').keys())

    def test_ContactPoint_model(self):
        contact = ContactPoint()

        self.assertEqual(contact.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'ContactPoint Model has no role "test"'):
            contact.serialize('test')

        with self.assertRaises(ModelValidationError) as ex:
            contact.validate()
        self.assertEqual(ex.exception.messages, {"name": ["This field is required."]})

        data = {"name": u"Державне управління справами",
                "telephone": u"0440000000"}

        contact.import_data({"name": data["name"]})
        with self.assertRaises(ModelValidationError) as ex:
            contact.validate()
        self.assertEqual(ex.exception.messages, {"email": ["telephone or email should be present"]})

        contact.import_data({"telephone": data["telephone"]})
        contact.validate()
        self.assertEqual(contact.serialize(), data)

        contact.telephone = None
        telephone = data.pop('telephone')
        with self.assertRaisesRegexp(ModelValidationError, 'email'):
            contact.validate()
        self.assertEqual(contact.serialize(), data)

        data.update({"email": 'qwe@example.test', "telephone": telephone})
        contact.import_data(data)
        contact.validate()
        self.assertEqual(contact.serialize(), data)

        contact.telephone = None
        contact.validate()
        self.assertNotEqual(contact.serialize(), data)
        data.pop('telephone')
        self.assertEqual(contact.serialize(), data)

    def test_Organization_model(self):

        data = {
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
        organization = Organization(data)
        organization.validate()

        self.assertEqual(organization.serialize(), data)
        with self.assertRaisesRegexp(ValueError, 'Organization Model has no role "test"'):
            organization.serialize('test')

        with mock.patch.dict('openprocurement.api.models.ocds.Identifier._options.roles', {'view': blacklist('id')}):
            self.assertNotEqual(organization.serialize('view'),
                                organization.serialize())
            self.assertIn('id', organization.serialize()['identifier'].keys())
            self.assertNotIn('id', organization.serialize('view')['identifier'].keys())

        additional_identifiers = []
        for _ in xrange(3):
            idtf = Identifier.get_mock_object()
            idtf.id = '0' * 6
            additional_identifiers.append(idtf.serialize())
        data['additionalIdentifiers'] = additional_identifiers

        organization2 = Organization(data)
        organization2.validate()

        self.assertNotEqual(organization, organization2)
        self.assertEqual(organization2.serialize(), data)

    def test_Document_model(self):

        data = {
            'title': u'укр.doc',
            'url': 'http://localhost/get',  # self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }

        document = BaseDocument()

        self.assertEqual(document.serialize('create'), None)
        self.assertEqual(document.serialize('edit'), None)
        with self.assertRaisesRegexp(ValueError, 'Document Model has no role "test"'):
            document.serialize('test')

        self.assertEqual(document.serialize().keys(),
                         ['dateModified', 'id', 'datePublished'])

        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(ex.exception.messages,
                         {"url": ["This field is required."],
                          "format": ["This field is required."],
                          "title": ["This field is required."]})

        document.import_data(data)
        document.validate()
        self.assertEqual(document.serialize('create'), data)
        self.assertEqual(document.serialize('edit'),
                         {'format': u'application/msword',
                          'title': u'\u0443\u043a\u0440.doc'})

        document.url = data['url'] = u'http://localhost/get/docs?download={}'.format(document.id)
        document.__parent__ = mock.MagicMock(**{
            '__parent__': mock.MagicMock(**{
                '__parent__': None,
                'request.registry.use_docservice': False})})
        document.validate()

        serialized_by_create = document.serialize('create')
        self.assertEqual(serialized_by_create.keys(),
                         ['url', 'format', 'hash', '__parent__', 'title'])
        serialized_by_create.pop('__parent__')
        self.assertEqual(serialized_by_create, data)


class DummyAuctionModelsTest(unittest.TestCase):
    """ Test Case for testing openprocurement.api.auction_models'
            - roles
            - serialization
            - validation
    """
    def test_Document_model(self):

        data = {
            'title': u'укр.doc',
            'url': 'http://localhost/get',  # self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }

        document = AuctionDocument()

        self.assertEqual(document.serialize('create'), None)
        self.assertEqual(document.serialize('edit'), None)
        with self.assertRaisesRegexp(ValueError, 'Document Model has no role "test"'):
            document.serialize('test')

        self.assertEqual(document.serialize().keys(),
                         ['url', 'dateModified', 'id', 'datePublished'])

        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(ex.exception.messages,
                         {"url": ["This field is required."],
                          "format": ["This field is required."],
                          "title": ["This field is required."]})

        document.import_data(data)
        document.validate()
        self.assertEqual(document.serialize('create'), data)
        self.assertEqual(document.serialize('edit'),
                         {'format': u'application/msword',
                          'title': u'\u0443\u043a\u0440.doc'})

        document.url = data['url'] = u'http://localhost/get/docs?download={}'.format(document.id)
        document.__parent__ = mock.MagicMock(**{
            '__parent__': mock.MagicMock(**{
                '__parent__': None,
                'request.registry.use_docservice': False})})
        document.validate()

        serialized_by_create = document.serialize('create')
        self.assertEqual(serialized_by_create.keys(),
                         ['url', 'format', 'hash', '__parent__', 'title'])
        serialized_by_create.pop('__parent__')
        self.assertEqual(serialized_by_create, data)


class DummyLokiModelsTest(unittest.TestCase):
    """ Test Case for testing openprocurement.api.models.registry_models.loki'
            - roles
            - serialization
            - validation
    """

    def test_Decision(self):
        data = {
            'decisionDate': now.isoformat(),
            'decisionID': 'decisionID'
        }

        decision = Decision()
        self.assertEqual(decision.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'Decision Model has no role "test"'):
            decision.serialize('test')

        with self.assertRaises(ModelValidationError) as ex:
            decision.validate()
        self.assertEqual(
            ex.exception.messages,
            {'decisionDate': [u'This field is required.'],
            'decisionID': [u'This field is required.']}
        )

        decision.import_data(data)
        decision.validate()

    def test_Document(self):
        data = {
            'title': u'укр.doc',
            'url': 'http://localhost/get',  # self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentType': 'notice'
        }

        document = LokiDocument()

        self.assertEqual(document.serialize('create'), None)
        self.assertEqual(document.serialize('edit'), None)
        with self.assertRaisesRegexp(ValueError, 'Document Model has no role "test"'):
            document.serialize('test')

        self.assertEqual(document.serialize().keys(),
                         ['dateModified', 'id', 'datePublished'])

        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(
            ex.exception.messages,
            {"title": ["This field is required."],
            "documentType": ["This field is required."]
             }
        )

        del data['format']
        del data['url']
        document.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                "url": ["This field is required."]
            }
        )

        data['format'] = 'application/msword'
        data['url'] = 'http://localhost/get'
        document.import_data(data)
        document.validate()


        self.assertEqual(document.serialize('create'), data)
        self.assertEqual(document.serialize('edit'),
                         {'format': data['format'],
                          'title': data['title'],
                          'documentType': data['documentType']
                          })

        document.url = data['url'] = u'http://localhost/get/docs?download={}'.format(document.id)
        document.__parent__ = mock.MagicMock(**{
            '__parent__': mock.MagicMock(**{
                '__parent__': None,
                'request.registry.use_docservice': False})})
        document.validate()

        serialized_by_create = document.serialize('create')
        self.assertEqual(
            set(serialized_by_create.keys()),
            set(['url', 'format', 'hash', '__parent__', 'title', 'documentType'])
        )
        serialized_by_create.pop('__parent__')
        self.assertEqual(serialized_by_create, data)

        data.update({'documentType': 'x_dgfAssetFamiliarization'})
        document.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                "accessDetails": [u"This field is required."],
                "hash": [u"This field is not required."],
                "url": [u"This field is not required."]
            }
        )
        offline_data = deepcopy(data)
        del offline_data['hash']
        del offline_data['url']
        offline_data.update({'accessDetails': 'Details'})
        document.import_data(offline_data)
        document.validate()
        data['accessDetails'] = None

        del offline_data['format']
        data.update({'accessDetails': 'Details'})
        document.import_data(offline_data)
        document.validate()
        data['accessDetails'] = None

        url_only_data = deepcopy(data)
        url_only_data['documentType'] = 'virtualDataRoom'
        del url_only_data['url']

        LokiDocument.documentType.choices = ['virtualDataRoom']
        document = LokiDocument()
        document.import_data(url_only_data)
        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                "format": [u"This field is not required."],
                "url": [u"This field is required."],
                "hash": [u"This field is not required."]
            }
        )

        url_only_data['url'] = 'http://localhost/get'
        del url_only_data['format']
        del url_only_data['hash']
        document.import_data(url_only_data)
        document.validate()

    def test_RegistrationDetails(self):
        registration_details = RegistrationDetails()

        self.assertEqual(registration_details.serialize(), {'status': 'unknown'})
        with self.assertRaisesRegexp(ValueError, 'RegistrationDetails Model has no role "test"'):
            registration_details.serialize('test')

        data = {
            'status': 'unknown'
        }
        registration_details.import_data(data)
        registration_details.validate()

        data.update({
            'registrationID': 'REG-ID',
            'registrationDate': now.isoformat()
        })
        registration_details.import_data(data)

        with self.assertRaises(ModelValidationError) as ex:
            registration_details.validate()
        self.assertEqual(
            ex.exception.messages,
            {'registrationID': [u'You can fill registrationID only when status is complete'],
            'registrationDate': [u'You can fill registrationDate only when status is complete']}
        )

        data['status'] = 'registering'
        registration_details.import_data(data)

        with self.assertRaises(ModelValidationError) as ex:
            registration_details.validate()
        self.assertEqual(
            ex.exception.messages,
            {'registrationID': [u'You can fill registrationID only when status is complete'],
            'registrationDate': [u'You can fill registrationDate only when status is complete']}
        )

        data['status'] = 'complete'
        registration_details.import_data(data)
        registration_details.validate()

    def test_Item(self):
        item = LokiItem()
        id_data = {'id': '1' * 32}
        item.import_data(id_data)

        self.assertEqual(item.serialize('create'), id_data)
        self.assertEqual(item.serialize('edit'), None)

        with self.assertRaises(ModelValidationError) as ex:
            item.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'registrationDetails': [u'This field is required.'],
                'description': [u'This field is required.'],
                'unit': [u'This field is required.'],
                'quantity': [u'This field is required.'],
                'classification': [u'This field is required.'],
                'address': [u'This field is required.'],
            }
        )


        loki_item_data = deepcopy(test_loki_item_data)
        loki_item_data['classification']['scheme'] = 'CAV'
        item = LokiItem(loki_item_data)

        with self.assertRaises(ModelValidationError) as ex:
            item.validate()
        self.assertEqual(
            ex.exception.messages,
            {'classification': {'scheme': [u"Value must be one of [u'CAV-PS', u'CPV']."]}}
        )

        loki_item_data = deepcopy(test_loki_item_data)
        loki_item_data['classification']['id'] = '07200000-1'
        item = LokiItem(loki_item_data)

        with self.assertRaises(ModelValidationError) as ex:
            item.validate()
        self.assertEqual(
            ex.exception.messages,
            {'classification':
                 {
                     'id': [
                         u'At least {} classification class (XXXX0000-Y) '
                         u'should be specified more precisely'.format(loki_item_data['classification']['scheme'])
                     ]
                 }
            }
        )

        loki_item_data = deepcopy(test_loki_item_data)
        loki_item_data['classification']['id'] = 'wrong-id'
        item = LokiItem(loki_item_data)


        with self.assertRaises(ModelValidationError) as ex:
            item.validate()

        available_codes = LOKI_ITEM_CLASSIFICATION.get('CAV-PS', [])
        err_string = BaseType.MESSAGES['choices'].format(unicode(available_codes))

        self.assertEqual(
            ex.exception.messages,
            {'classification': {'id': [err_string]}}
        )

        loki_item_data = deepcopy(test_loki_item_data)
        item = LokiItem(loki_item_data)
        item.validate()
        self.assertEqual(item.serialize()['description'], loki_item_data['description'])
        self.assertEqual(item.serialize()['classification'], loki_item_data['classification'])
        self.assertEqual(item.serialize()['additionalClassifications'], loki_item_data['additionalClassifications'])
        self.assertEqual(item.serialize()['address'], loki_item_data['address'])
        self.assertEqual(item.serialize()['id'], loki_item_data['id'])
        self.assertEqual(item.serialize()['unit'], loki_item_data['unit'])
        self.assertEqual(float(item.serialize()['quantity']), loki_item_data['quantity'])
        self.assertEqual(item.serialize()['registrationDetails'], loki_item_data['registrationDetails'])

        with self.assertRaisesRegexp(ValueError, 'Item Model has no role "test"'):
            item.serialize('test')

        loki_item_data['location'] = {'latitude': '123', 'longitude': '567'}
        item2 = LokiItem(loki_item_data)
        item2.validate()

        self.assertNotEqual(item, item2)
        item2.location = None
        self.assertEqual(item, item2)

        loki_item_data['schema_properties'] = {
            u"code": "04000000-8",
            u"version": "latest",
            u"properties": {
                u"totalArea": 200,
                u"year": 1998,
                u"floor": 3
            }
        }

        item3 = LokiItem(loki_item_data)
        with self.assertRaises(ModelValidationError) as ex:
            item3.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'schema_properties': [u'Opportunity to use schema_properties is disabled'],
            }
        )
        # item3.validate()

    def test_AssetCustodian(self):
        data = {
            'name': 'Name'
        }

        asset_custodian = AssetCustodian()
        self.assertEqual(asset_custodian.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'AssetCustodian Model has no role "test"'):
            asset_custodian.serialize('test')

        asset_custodian.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            asset_custodian.validate()
        self.assertEqual(
            ex.exception.messages,
            {'contactPoint': [u'This field is required.'],
            'identifier': [u'This field is required.'],
            'address': [u'This field is required.']
             }
        )
        data = {
            'contactPoint': {'name': 'name'},
            'identifier': {'scheme': 'UA-EDR', 'id': '22222-2'},
            'address': {'countryName': 'country name'}
        }
        asset_custodian.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            asset_custodian.validate()
        self.assertEqual(
            ex.exception.messages,
            {'contactPoint': {'email': [u'telephone or email should be present']}
             }
        )
        data['contactPoint'] = {'name': 'name', 'telephone': '12345543'}

        asset_custodian.import_data(data)
        asset_custodian.validate()

        data.update({
            'additionalContactPoints': [
                {'name': 'name', 'email': 'some@mail.com'}
            ]
        })
        asset_custodian.import_data(data)
        asset_custodian.validate()


    def test_AssetHolder(self):
        data = {
            'name': 'Name',
            'identifier': {
                'legalName_ru': "Some name"
            }
        }

        asset_holder = AssetHolder()
        self.assertEqual(asset_holder.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'AssetHolder Model has no role "test"'):
            asset_holder.serialize('test')

        with self.assertRaises(ModelValidationError) as ex:
            asset_holder.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'identifier': [u'This field is required.'],
                'name': [u'This field is required.']
            }
        )

        asset_holder.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            asset_holder.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'identifier': {
                    'scheme': [u'This field is required.'],
                    'id': [u'This field is required.'],
                }
            }
        )
        data.update({
            'identifier': {
                'scheme': 'UA-EDR',
                'id': 'justID'
            }})
        asset_holder.import_data(data)
        asset_holder.validate()

        data.update({
            'additionalContactPoints': [
                {'name': 'name', 'email': 'some@mail.com'}
            ]
        })
        asset_holder.import_data(data)
        asset_holder.validate()


class AppSchemaModelsTest(unittest.TestCase):
    """ Test Case for testing openprocurement.api.config'
    """

    def test_Main_defaults(self):
        main = Main()

        main.validate()

        self.assertEqual(main.serialize()['server_id'], '')
        self.assertNotIn('api_version', main.serialize())

    def test_Main_valid_values(self):
        main_data = deepcopy(test_config_data['config']['main'])
        main = Main(main_data)

        main.validate()

        self.assertEqual(main.serialize()['server_id'], '')
        self.assertEqual(
            main.serialize()['api_version'], main_data['api_version']
        )

    def test_Auth_empty(self):
        auth = Auth()

        with self.assertRaises(ModelValidationError) as ex:
            auth.validate()

        self.assertEqual(
            ex.exception.messages,
            {'type': [u'This field is required.']}
        )

    def test_Auth_valid_values(self):
        auth_data = deepcopy(test_config_data['config']['auth'])
        auth = Auth(auth_data)

        auth.validate()

        self.assertEqual(auth.serialize()['type'], auth_data['type'])
        self.assertEqual(auth.serialize()['src'], auth_data['src'])

    def test_Auth_unsupported_type(self):
        auth_data = deepcopy(test_config_data['config']['auth'])
        auth_data['type'] = 'test'
        auth = Auth(auth_data)

        with self.assertRaises(ModelValidationError) as ex:
            auth.validate()

        self.assertEqual(
            ex.exception.messages,
            {"type": [u"Value must be one of {}.".format(
                str(Auth.type.choices)
            )]}
        )

    def test_Auth_void_type(self):
        auth_data = deepcopy(test_config_data['config']['auth'])
        auth_data['type'] = 'void'
        auth = Auth(auth_data)

        auth.validate()

        self.assertEqual(auth.serialize()['type'], auth_data['type'])
        self.assertEqual(auth.serialize()['src'], auth_data['src'])

    def test_Auth_void_type_without_source(self):
        auth_data = deepcopy(test_config_data['config']['auth'])
        auth_data['type'] = 'void'
        auth_data.pop('src', None)
        auth = Auth(auth_data)

        auth.validate()

        self.assertEqual(auth.serialize()['type'], auth_data['type'])
        self.assertEqual(auth.serialize()['src'], None)

    def test_User_empty(self):
        user = User()

        with self.assertRaises(ModelValidationError) as ex:
            user.validate()

        self.assertEqual(
            ex.exception.messages,
            {'name': [u'This field is required.'],
             'password': [u'This field is required.']}
        )

    def test_User_valid_values(self):
        user_data = deepcopy(test_user_data)
        user = User(user_data)

        user.validate()

        self.assertEqual(user.serialize()['name'], user_data['name'])
        self.assertEqual(user.serialize()['password'], user_data['password'])

    def test_DefaultWriter_defaults(self):
        user = DefaultWriter()

        user.validate()

        self.assertEqual(user.serialize()['name'], 'op')
        self.assertEqual(user.serialize()['password'], 'op')

    def test_DB_empty(self):
        db = DB()

        with self.assertRaises(ModelValidationError) as ex:
            db.validate()

        self.assertEqual(
            ex.exception.messages,
            {'type': [u'This field is required.'],
             'db_name': [u'This field is required.'],
             'url': [u'This field is required.']}
        )

    def test_DB_valid_values_without_admin(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db = DB(db_data)

        db.validate()

        self.assertEqual(db.serialize()['type'], db_data['type'])
        self.assertEqual(db.serialize()['db_name'], db_data['db_name'])
        self.assertEqual(db.serialize()['url'], db_data['url'])
        self.assertEqual(db.serialize()['admin'], None)
        self.assertEqual(db.serialize()['reader'], None)
        self.assertEqual(db.serialize()['writer']['name'], 'op')
        self.assertEqual(db.serialize()['writer']['password'], 'op')

    def test_DB_create_url_method_invalid_arg(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db = DB(db_data)

        with self.assertRaises(ValidationError) as ex:
            db.create_url('test')

        self.assertEqual(
            ex.exception.messages,
            ["Value must be on of ['admin', 'reader', 'writer']"]
        )

    def test_DB_create_url_method_invalid_arg_missing_field(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db = DB(db_data)

        with self.assertRaises(ValidationError) as ex:
            db.create_url('reader')

        self.assertEqual(
            ex.exception.messages,
            ["Field 'reader' is not specified"]
        )

    def test_DB_create_url_method_without_scheme(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db = DB(db_data)

        url = db.create_url('writer')

        self.assertEqual(url, 'http://op:op@localhost:5984')

    def test_DB_create_url_method_with_scheme(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db = DB(db_data)
        db.url = "http://localhost:5984"

        url = db.create_url('writer')

        self.assertEqual(url, 'http://op:op@localhost:5984')

    def test_DB_missing_reader_field(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db_data['admin'] = deepcopy(test_user_data)
        db = DB(db_data)

        with self.assertRaises(ModelValidationError) as ex:
            db.validate()

        self.assertEqual(
            ex.exception.messages,
            {'reader': [u'This field is required.']}
        )

    def test_DB_valid_values_with_admin(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db_data['admin'] = deepcopy(test_user_data)
        db_data['reader'] = deepcopy(test_user_data)
        db = DB(db_data)

        db.validate()

        self.assertEqual(
            db.serialize()['reader']['name'], db_data['reader']['name']
        )
        self.assertEqual(
            db.serialize()['reader']['password'], db_data['reader']['password']
        )
        self.assertEqual(
            db.serialize()['admin']['name'], db_data['admin']['name']
        )
        self.assertEqual(
            db.serialize()['admin']['password'], db_data['admin']['password']
        )

    def test_DB_unsupported_type(self):
        db_data = deepcopy(test_config_data['config']['db'])
        db_data['type'] = 'postgresql'
        db = DB(db_data)

        with self.assertRaises(ModelValidationError) as ex:
            db.validate()

        self.assertEqual(
            ex.exception.messages,
            {"type": [u"Value must be one of ['couchdb']."]}
        )

    def test_DS_empty(self):
        ds = DS()

        with self.assertRaises(ModelValidationError) as ex:
            ds.validate()

        self.assertEqual(
            ex.exception.messages,
            {'user': [u'This field is required.'],
             'download_url': [u'This field is required.'],
             'dockeys': [u'This field is required.']}
        )

    def test_DS_valid_values(self):
        ds_data = deepcopy(test_config_data['config']['ds'])
        ds = DS(ds_data)

        ds.validate()

        self.assertEqual(
            ds.serialize()['user']['name'], ds_data['user']['name']
        )
        self.assertEqual(
            ds.serialize()['user']['password'], ds_data['user']['password']
        )
        self.assertEqual(
            ds.serialize()['download_url'], ds_data['download_url']
        )
        self.assertEqual(
            ds.signer.hex_seed(), Signer(ds.dockey.decode('hex')).hex_seed()
        )
        self.assertEqual(ds.serialize()['upload_url'], None)
        self.assertEqual(ds.serialize()['dockey'], ds_data['dockey'])
        self.assertEqual(ds.serialize()['dockeys'], ds_data['dockeys'])

    def test_DS_init_keyring_method(self):
        ds_data = deepcopy(test_config_data['config']['ds'])
        ds = DS(ds_data)
        keyring1 = {}
        for key in ds.dockeys:
            keyring1[key[:8]] = Verifier(key)

        keyring2 = ds.init_keyring(ds.signer)

        self.assertEqual(keyring1.viewkeys(), keyring2.viewkeys())

    def test_DS_invalid_values(self):
        ds_data = deepcopy(test_config_data['config']['ds'])
        ds = DS(ds_data)
        ds.dockey = 'abc123'
        ds.dockeys = ['123']

        with self.assertRaises(ValidationError) as ex:
            ds.validate()

        self.assertEqual(
            ex.exception.messages,
            {'dockey': ['Invalid seed bytes'],
             'dockeys': [['Odd-length string']]}
        )

    def test_AuctionModule_empty(self):
        auction_module = AuctionModule()

        with self.assertRaises(ModelValidationError) as ex:
            auction_module.validate()

        self.assertEqual(
            ex.exception.messages,
            {'url': [u'This field is required.'],
             'public_key': [u'This field is required.']}
        )

    def test_AuctionModule_valid_values(self):
        auction_module_data = deepcopy(test_config_data['config']['auction'])
        auction_module = AuctionModule(auction_module_data)

        auction_module.validate()

        self.assertEqual(
            auction_module.serialize()['url'], auction_module['url']
        )
        self.assertEqual(
            auction_module.serialize()['public_key'],
            auction_module['public_key']
        )
        self.assertEqual(
            auction_module.signer.hex_seed(),
            Signer(auction_module.public_key.decode('hex')).hex_seed()
        )

    def test_AuctionModule_invalid_public_key_seed_bytes(self):
        auction_module_data = deepcopy(test_config_data['config']['auction'])
        auction_module = AuctionModule(auction_module_data)
        auction_module.public_key = 'abc123'

        with self.assertRaises(ValidationError) as ex:
            auction_module.validate()

        self.assertEqual(
            ex.exception.messages,
            {'public_key': ['Invalid seed bytes']}
        )

    def test_AuctionModule_invalid_public_key_string_length(self):
        auction_module_data = deepcopy(test_config_data['config']['auction'])
        auction_module = AuctionModule(auction_module_data)
        auction_module.public_key = '123'

        with self.assertRaises(ValidationError) as ex:
            auction_module.validate()

        self.assertEqual(
            ex.exception.messages,
            {'public_key': ['Odd-length string']}
        )

    def test_Config_empty(self):
        config = Config()

        with self.assertRaises(ModelValidationError) as ex:
            config.validate()

        self.assertEqual(
            ex.exception.messages,
            {'auth': [u'This field is required.'],
             'db': [u'This field is required.']}
        )

    def test_Config_valid_values(self):
        config_data = deepcopy(test_config_data['config'])
        config = Config(config_data)

        config.validate()

        self.assertEqual(
            config.serialize().keys(), ['auction', 'main', 'db', 'ds', 'auth']
        )

    def test_Config_valid_values_auto_generated_main(self):
        config_data = deepcopy(test_config_data['config'])
        config_data.pop('main')
        config = Config(config_data)

        config.validate()

        self.assertEqual(config.serialize()['main'], {'server_id': u''})

    def test_AppMetaSchema_empty(self):
        app_meta = AppMetaSchema()

        with self.assertRaises(ModelValidationError) as ex:
            app_meta.validate()

        self.assertEqual(
            ex.exception.messages,
            {'config': [u'This field is required.'],
             'plugins': [u'This field is required.'],
             'here': [u'This field is required.']}
        )

    def test_AppMetaSchema_valid_values(self):
        app_meta_data = deepcopy(test_config_data)
        app_meta = AppMetaSchema(app_meta_data)

        app_meta.validate()

        self.assertEqual(app_meta.serialize()['plugins'], {})
        self.assertEqual(app_meta.serialize()['here'], os.getcwd())


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(DummyOCDSModelsTest))
    tests.addTest(unittest.makeSuite(DummyAuctionModelsTest))
    tests.addTest(unittest.makeSuite(SchematicsExtenderTest))
    tests.addTest(unittest.makeSuite(AppSchemaModelsTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
