# -*- coding: utf-8 -*-
import mock
import unittest

from datetime import timedelta, datetime
from cornice.errors import Errors
from couchdb.client import Document
from libnacl.sign import Signer
from pyramid.config import Configurator
from uuid import UUID

from openprocurement.api.utils import (
    apply_data_patch,
    context_unpack,
    error_handler,
    decrypt, encrypt,
    forbidden,
    generate_docservice_url,
    generate_id,
    get_content_configurator,
    get_revision_changes,
    load_plugins,
    prepare_patch,
    set_modetest_titles,
    set_ownership,
    set_parent,
    update_logging_context,
    calculate_business_date,
    get_now,
)


class UtilsTest(unittest.TestCase):

    def test_generate_id(self):
        id = generate_id()

        self.assertEqual(len(id), 32)
        self.assertEqual(type(UUID(id)), UUID)

    def test_error_handler(self):
        errors = Errors(403)
        errors.add('body', 'data', "Can't update resource in current (draft) status")

        request = mock.MagicMock()
        request.matchdict = {'a': 'b'}
        request.errors = errors
        response = error_handler(request)

        self.assertEqual(response.body, '{"status": "error", "errors": [{"location": "body", "name": "data", "description": "Can\'t update resource in current (draft) status"}]}')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')

    def test_forbidden(self):
        request = mock.MagicMock()
        request.errors = Errors()
        response = forbidden(request)

        self.assertEqual(response.body, '{"status": "error", "errors": [{"location": "url", "name": "permission", "description": "Forbidden"}]}')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')

    # def test_raise_operation_error(self):
    #     request = mock.MagicMock()
    #     request.errors = Errors()
    #     response = raise_operation_error(request, error_handler, message="Can't update resource in current (draft) status")
    #
    #     self.assertEqual(response.body, '{"status": "error", "errors": [{"location": "body", "name": "data", "description": "Can\'t update resource in current (draft) status"}]}')
    #     self.assertEqual(response.content_type, 'application/json')
    #     self.assertEqual(response.status, '403 Forbidden')

    def test_get_revision_changes(self):
        dst = {
            'status': u'draft',
            'assetType': u'basic',
            'classification': {'scheme': u'CAV',
                               'description': u'\u0417\u0435\u043c\u0435\u043b\u044c\u043d\u0456 \u0434\u0456\u043b\u044f\u043d\u043a\u0438',
                               'id': u'39513200-3'},
            'title': u'\u0417\u0435\u043c\u043b\u044f \u0434\u043b\u044f \u043a\u043e\u0441\u043c\u043e\u0434\u0440\u043e\u043c\u0443',
            'assetID': 'UA-2017-08-16-000001',
            'value': {'currency': u'UAH', 'amount': 100.0,
                      'valueAddedTaxIncluded': True},
            'date': '2017-08-16T12:30:17.615196+03:00',
            'owner_token': '4bc0ddbd9df1261da3f9c30fc920e9aa0f8e22f52567e7f8c42d8962b89b629acea680a4d53206eb7627f155995d4295ca0970769afed83fb398db0cc1432ea0',
            'unit': {'code': u'39513200-3', 'name': u'item'},
            'address': {
                'postalCode': u'79000',
                'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430',
                'streetAddress': u'\u0432\u0443\u043b. \u0411\u0430\u043d\u043a\u043e\u0432\u0430 1',
                'region': u'\u043c. \u041a\u0438\u0457\u0432',
                'locality': u'\u043c. \u041a\u0438\u0457\u0432',
            },
            'owner': 'broker',
            'id': '625699bf9d5b4f098772d5cafee283fe',
            'assetCustodian': {
                'contactPoint': {
                    'name': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u0443\u043f\u0440\u0430\u0432\u043b\u0456\u043d\u043d\u044f \u0441\u043f\u0440\u0430\u0432\u0430\u043c\u0438',
                    'telephone': u'0440000000'},
                'identifier': {'scheme': u'UA-EDR', 'id': u'00037256',
                               'uri': u'http://www.dus.gov.ua/'},
                'name': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u0443\u043f\u0440\u0430\u0432\u043b\u0456\u043d\u043d\u044f \u0441\u043f\u0440\u0430\u0432\u0430\u043c\u0438',
                'address': {
                    'postalCode': u'01220',
                    'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430',
                    'streetAddress': u'\u0432\u0443\u043b. \u0411\u0430\u043d\u043a\u043e\u0432\u0430, 11, \u043a\u043e\u0440\u043f\u0443\u0441 1',
                    'region': u'\u043c. \u041a\u0438\u0457\u0432',
                    'locality': u'\u043c. \u041a\u0438\u0457\u0432',
                },
            },
            'quantity': 5,
        }

        src = {
            "status": u"pending",
            "new_field": {
                "subfield_1": u"value_1",
                "subfield_2": u"value_2",
            }
        }

        expected_result = [
            {u'op': u'remove', u'path': u'/assetType', u'value': dst['assetType']},
            {u'op': u'remove', u'path': u'/classification', u'value': dst['classification']},
            {u'op': u'remove', u'path': u'/title', u'value': dst['title']},
            {u'op': u'remove', u'path': u'/assetID', u'value': dst['assetID']},
            {u'op': u'remove', u'path': u'/value', u'value': dst['value']},
            {u'op': u'remove', u'path': u'/date', u'value': dst['date']},
            {u'op': u'remove', u'path': u'/owner_token', u'value': dst['owner_token']},
            {u'op': u'remove', u'path': u'/unit', u'value': dst['unit']},
            {u'op': u'remove', u'path': u'/address', u'value': dst['address']},
            {u'op': u'remove', u'path': u'/owner', u'value': dst['owner']},
            {u'op': u'remove', u'path': u'/id', u'value': dst['id']},
            {u'op': u'remove', u'path': u'/assetCustodian', u'value': dst['assetCustodian']},
            {u'op': u'remove', u'path': u'/quantity', u'value': dst['quantity']},
            {u'op': u'add',
             u'path': u'/new_field',
             u'value': src['new_field']},
            {u'op': u'replace', u'path': u'/status', u'value': src['status']},
        ]

        result = get_revision_changes(dst=dst, src=src)
        # Make sorting because get_revision_changes can return
        # proper results but ordering will be differ from expected result
        # and test will fail
        result = result.sort(key=lambda r: r['path'])
        expected_result = expected_result.sort(key=lambda r: r['path'])
        self.assertEqual(result, expected_result)

    def test_apply_data_patch(self):
        item = Document({
            u'status': u'draft',
            u'assetType': u'basic',
            u'doc_type': u'Asset'
        })
        changes = {'status': 'pending'}
        expected_result = Document({
            u'status': 'pending',
            u'assetType': u'basic',
            u'doc_type': u'Asset'
        })
        result = apply_data_patch(item=item, changes=changes)
        self.assertEqual(result, expected_result)

        changes = {}
        result = apply_data_patch(item=item, changes=changes)
        self.assertEqual(result, {})

    def test_set_parent(self):
        item = mock.MagicMock()
        parent = mock.MagicMock()

        item.__parent__ = 'not_none_value'
        set_parent(item=item, parent=parent)
        self.assertEqual(item.__parent__, 'not_none_value')

        item.__parent__ = None
        set_parent(item=item, parent=parent)
        self.assertEqual(item.__parent__, parent)

    def test_encrypt(self):
        kwargs = {
            "key": 42,
            "name": 'tests1234567890abcdef1234567890abcdef',
            "uuid": 'af41bf2254c843dcb0a0a9703af1cb88'
        }
        expected_result = 'cc10fa135532b71490f46ee2cec71dc8'
        result = encrypt(**kwargs)
        self.assertEqual(result, expected_result)

        kwargs["key"] = 15
        kwargs["uuid"] = 'f88fcd9409844824bd45cb446abf4a30'
        expected_result = 'd1b61eed6805bff35bbc28cf6ea39cc9'
        result = encrypt(**kwargs)
        self.assertEqual(result, expected_result)

    def test_decrypt(self):
        kwargs = {
            "key": 'cc10fa135532b71490f46ee2cec71dc8',
            "name": 'tests1234567890abcdef1234567890abcdef',
            "uuid": 'af41bf2254c843dcb0a0a9703af1cb88'
        }
        expected_result = '42'
        result = decrypt(**kwargs)
        self.assertEqual(result, expected_result)

        kwargs["key"] = 'd1b61eed6805bff35bbc28cf6ea39cc9'
        kwargs["uuid"] = 'f88fcd9409844824bd45cb446abf4a30'
        expected_result = '15'
        result = decrypt(**kwargs)
        self.assertEqual(result, expected_result)

        kwargs["key"] = '0'
        result = decrypt(**kwargs)
        self.assertEqual(result, '')

    # def test_get_now(self):
    #     TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')
    #     self.assertAlmostEqual(get_now(), datetime.now(TZ))

    def test_set_modetest_titles(self):

        class Item(object):
            def __init__(self, title=None):
                self.title = title
                self.title_en = title
                self.title_ru = title

        item = Item('test')
        set_modetest_titles(item)

        self.assertEqual(item.title, u'[\u0422\u0415\u0421\u0422\u0423\u0412\u0410\u041d\u041d\u042f] test')
        self.assertEqual(item.title_en, u'[TESTING] test')
        self.assertEqual(item.title_ru, u'[\u0422\u0415\u0421\u0422\u0418\u0420\u041e\u0412\u0410\u041d\u0418\u0415] test')

    def test_update_logging_context(self):
        request = mock.MagicMock()
        params = {"test_field": "test_value"}
        update_logging_context(request, params)
        self.assertEqual(request.logging_context, {'TEST_FIELD': 'test_value'})

        request.logging_context = {"A": 'b'}
        update_logging_context(request, params)
        self.assertEqual(request.logging_context, {'A': 'b', 'TEST_FIELD': 'test_value'})

    def test_context_unpack(self):
        request = mock.MagicMock()
        request.logging_context = {"A": 'b'}
        msg = {'MESSAGE_ID': 'test'}

        expected_result = {'JOURNAL_A': 'b', 'MESSAGE_ID': 'test'}
        result = context_unpack(request, msg)
        self.assertAlmostEqual(result, expected_result)

        expected_result = {'JOURNAL_C': 'd', 'JOURNAL_A': 'b', 'MESSAGE_ID': 'test'}
        result = context_unpack(request, msg, {'c': 'd'})
        self.assertAlmostEqual(result, expected_result)

    @mock.patch('openprocurement.api.utils.generate_id')
    def test_set_ownership(self, mock_generate_id):
        request = mock.MagicMock()
        mock_generate_id.return_value = '1234567890abcdef1234567890abcdef'
        # '0f20c55ac78f7336576260487b865a89a72b396d761ac69d00902cf5bd021d1c51b17191098dc9626f4582ab125efd9053fff1c8b58782e2fe70f7cb4b7bd7ee'

        class Item(object):
            transfer_token = None

            def __init__(self, owner=None):
                self.owner = owner

            def get(self, _):
                if self.owner:
                    return self.owner
                else:
                    return self.owner

        item = Item()
        expected_result = {'token': '1234567890abcdef1234567890abcdef'}
        result = set_ownership(item, request)
        self.assertEqual(result, expected_result)
        self.assertEqual(item.owner_token, '0f20c55ac78f7336576260487b865a89a72b396d761ac69d00902cf5bd021d1c51b17191098dc9626f4582ab125efd9053fff1c8b58782e2fe70f7cb4b7bd7ee')

        # with mock.patch('__builtin__.getattr') as mock_getattr:
        #     mock_getattr.return_value = True
        #     expected_result = {'token': '1234567890abcdef1234567890abcdef', 'transfer': '1234567890abcdef1234567890abcdef'}
        #     result = set_ownership(item, request)
        #     self.assertEqual(result, expected_result)
        #     self.assertEqual(item.transfer_token, '0f20c55ac78f7336576260487b865a89a72b396d761ac69d00902cf5bd021d1c51b17191098dc9626f4582ab125efd9053fff1c8b58782e2fe70f7cb4b7bd7ee')

    def test_get_content_configurator(self):
        request = mock.MagicMock()
        request.path = '/api/0.1/assets/e564ccab91d14029afe1011305ac024b'
        request.content_type = 'application/json'
        request.registry.queryMultiAdapter = mock.MagicMock()
        request.registry.queryMultiAdapter.return_value = 'configuration_adapter'

        result = get_content_configurator(request)
        self.assertEqual(result, 'configuration_adapter')
        self.assertEqual(request.registry.queryMultiAdapter._mock_call_count, 1)

    def test_generate_docservice_url(self):
        request = mock.MagicMock()
        request.registry = mock.MagicMock()
        request.registry.docservice_key = Signer('1234567890abcdef1234567890abcdef')
        request.registry.docservice_url = 'url'

        expected_result = '/get/1234567890abcdef1234567890abcdef?KeyID=c6c4f29c&Signature=t8L5VW%252BK5vvDwMsxHBhzs%252BcBXFsYAZ%2FM9WJmzgYLVpc8HC9mPbQhsshgGK94XaCtvKFTb9IiTLlW59TM9mV7Bg%253D%253D'
        result = generate_docservice_url(request, '1234567890abcdef1234567890abcdef', False)
        self.assertEqual(result, expected_result)

        expected_result = [
            '/get/1234567890abcdef1234567890abcdef?Prefix=test_prefix',
            '&KeyID=c6c4f29c&Signature=',
            '&Expires='
        ]
        result = generate_docservice_url(request, '1234567890abcdef1234567890abcdef', True, 'test_prefix')
        for item in expected_result:
            self.assertIn(item, result)

    @mock.patch('pkg_resources.iter_entry_points')
    @mock.patch('openprocurement.api.includeme.includeme')
    def test_load_plugins(self, mock_includeme, mock_iter_entry_points):
        config = Configurator()
        group = 'openprocurement.api.plugins'
        kwargs = {'plugins': ['api']}
        entry_point = mock.MagicMock()
        entry_point.name = 'api'
        mock_iter_entry_points.return_value = entry_point
        load_plugins(config, group, **kwargs)

        mock_includeme.assert_called_once_with(config)

    def test_prepare_patch(self):
        changes = []
        orig = Document({
            u'status': u'draft',
            u'assetType': u'basic',
            u'doc_type': u'Asset'
        })
        patch = {'status': 'pending'}

        prepare_patch(changes, orig, patch)
        self.assertEqual(changes, [{u'path': '/status', u'value': 'pending', u'op': u'replace'}])

        changes.pop()
        del orig[u'status']

        prepare_patch(changes, orig, patch)
        self.assertEqual(changes, [{'path': '/status', 'value': 'pending', 'op': 'add'}])


class CalculateBusinessDateTestCase(unittest.TestCase):

    def auction_mock(self, procurementMethodDetails):
        """Returns auction mock for accelerated mode testing.
        """
        auction = mock.MagicMock()
        acceleration_field = {'procurementMethodDetails': procurementMethodDetails}

        auction.__getitem__.side_effect = acceleration_field.__getitem__
        auction.__iter__.side_effect = acceleration_field.__iter__
        auction.__contains__.side_effect = acceleration_field.__contains__

        return auction

    def test_accelerated_calculation(self):
        auction = self.auction_mock(procurementMethodDetails='quick, accelerator=1440')
        start = get_now()
        period_to_add = timedelta(days=1440)
        result = calculate_business_date(start, period_to_add, context=auction)
        
        self.assertEqual((result - start).days, 1)

    def test_common_calculation_with_working_days(self):
        """This test assumes that <Mon 2018-4-9> is holiday, besides regular holidays
        of that month. It must be fixed in `working_days.json` file, that translates
        into `WORKING_DAYS` constant.
        """
        start = datetime(2018, 4, 2)
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17)
        result = calculate_business_date(start, business_days_to_add, working_days=True)

        self.assertEqual(result, target_end_of_period)

    def test_calculate_with_negative_time_period(self):
        start = datetime(2018, 4, 17)
        business_days_to_add = timedelta(days=-10)
        target_end_of_period = datetime(2018, 4, 2)
        result = calculate_business_date(start, business_days_to_add, working_days=True)

        self.assertEqual(result, target_end_of_period)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UtilsTest))
    suite.addTest(unittest.makeSuite(CalculateBusinessDateTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
