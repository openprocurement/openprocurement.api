# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal

import mock
from isodate.duration import Duration
from openprocurement.api.models.registry_models.roles import blacklist
from openprocurement.api.models.schematics_extender import DecimalType
from openprocurement.api.models.registry_models.ocds import (
    Organization,
    ContactPoint,
    Identifier,
    Address,
    BaseItem,
    Location,
    Unit,
    Value,
    ItemClassification,
    Classification,
    BaseDocument,
    LokiDocument,
    RegistrationDetails,
    LokiItem,
    AssetCustodian,
    AssetHolder,
    Decision,
)
from openprocurement.api.models.auction_models.models import (
    Document as AuctionDocument
)
from openprocurement.api.models.models import Period, PeriodEndRequired
from openprocurement.api.models.schematics_extender import (
    IsoDateTimeType, HashType, IsoDurationType)
from openprocurement.api.tests.blanks.json_data import (
    test_item_data_with_schema,
    test_loki_item_data
)
from openprocurement.api.utils import get_now
from schematics.exceptions import ConversionError, ValidationError, ModelValidationError

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

        with mock.patch.dict('openprocurement.api.models.registry_models.ocds.BaseItem._options.roles', {'test': blacklist('__parent__', 'address')}):
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

        with mock.patch.dict('openprocurement.api.models.registry_models.ocds.Identifier._options.roles', {'test': blacklist('id')}):
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

        with mock.patch.dict('openprocurement.api.models.registry_models.ocds.Identifier._options.roles', {'view': blacklist('id')}):
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
                'request.registry.docservice_url': None})})
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
                'request.registry.docservice_url': None})})
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
        }

        document = LokiDocument()

        self.assertEqual(document.serialize('create'), None)
        self.assertEqual(document.serialize('edit'), None)
        with self.assertRaisesRegexp(ValueError, 'Document Model has no role "test"'):
            document.serialize('test')

        self.assertEqual(document.serialize().keys(),
                         ['url', 'dateModified', 'id', 'datePublished'])

        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(
            ex.exception.messages,
            {"url": ["This field is required."],
            "title": ["This field is required."]}
        )

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
                'request.registry.docservice_url': None})})
        document.validate()

        serialized_by_create = document.serialize('create')
        self.assertEqual(serialized_by_create.keys(),
                         ['url', 'format', 'hash', '__parent__', 'title'])
        serialized_by_create.pop('__parent__')
        self.assertEqual(serialized_by_create, data)

        data.update({'documentType': 'x_dgfAssetFamiliarization'})
        document.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            document.validate()
        self.assertEqual(
            ex.exception.messages,
            {"accessDetails": [u"accessDetails is required, when documentType is x_dgfAssetFamiliarization"]}
        )

        data.update({'accessDetails': 'Details'})
        document.import_data(data)
        document.validate()
        data['accessDetails'] = None

    def test_RegistrationDetails(self):
        registration_details = RegistrationDetails()

        self.assertEqual(registration_details.serialize(), None)
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

        data['status'] = 'proceed'
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

        self.assertEqual(item.serialize('create'), None)
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
            {'name': [u'This field is required.'],
            'identifier': [u'This field is required.']}
        )

        asset_holder.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            asset_holder.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'identifier': {
                    'uri': [u'This field is required.'],
                    'legalName': [u'This field is required.'],
                    'id': [u'This field is required.']
                }
            }
        )
        data.update({
            'identifier': {
                'legalName': 'Legal Name',
                'uri': 'https://localhost/someuri',
                'id': 'justID'
            }})
        asset_holder.import_data(data)
        asset_holder.validate()


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(DummyOCDSModelsTest))
    tests.addTest(unittest.makeSuite(DummyAuctionModelsTest))
    tests.addTest(unittest.makeSuite(SchematicsExtenderTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
