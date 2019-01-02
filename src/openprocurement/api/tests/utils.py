# -*- coding: utf-8 -*-
import os
import mock
import unittest
import iso8601

from datetime import timedelta, datetime, date, time
from hashlib import sha512
from uuid import UUID
from pytz import timezone, utc
from copy import deepcopy

from cornice.errors import Errors
from couchdb.client import Document
from libnacl.sign import Signer
from schematics.types import StringType

from openprocurement.api.utils.common import (
    apply_data_patch,
    calculate_business_date,
    call_before,
    collect_packages_for_migration,
    connection_mock_config,
    context_unpack,
    create_app_meta,
    decrypt,
    dump_dict_to_tempfile,
    encrypt,
    error_handler,
    forbidden,
    format_aliases,
    generate_docservice_url,
    generate_id,
    get_content_configurator,
    get_file_path,
    get_now,
    get_plugin_aliases,
    get_revision_changes,
    make_aliases,
    path_to_kv,
    prepare_patch,
    round_seconds_to_hours,
    run_migrations_console_entrypoint,
    search_list_with_dicts,
    set_modetest_titles,
    set_ownership,
    set_parent,
    set_timezone,
    update_logging_context,
    utcoffset_difference,
    utcoffset_is_aliquot_to_hours,
)
from openprocurement.api.constants import TZ
from openprocurement.api.exceptions import ConfigAliasError
from openprocurement.api.tests.base import MOCK_CONFIG
from openprocurement.api.tests.fixtures.config import RANDOM_PLUGINS


class UtilsTest(unittest.TestCase):

    class OwnershipTestItem(object):
        transfer_token = StringType()

        def __init__(self, owner=None):
            self.owner = owner

        def get(self, _):
            return self.owner

    # Mock data for aliases helper functions.
    ALIASES_MOCK_DATA = {
        'auctions.rubble.financial': {'use_default': True, 'migration': False, 'aliases': ['Alias']}
    }

    def test_format_aliases(self):
        result = format_aliases({'auctions.rubble.financial': ['Alias']})
        self.assertEqual(result, "auctions.rubble.financial aliases: ['Alias']")

    def test_get_plugin_error(self):
        data = {'auctions.rubble.financial': {'aliases': ['One', 'One']}}
        with self.assertRaises(ConfigAliasError):
            get_plugin_aliases(data)

    def test_make_alias(self):
        data = {'auctions.rubble.financial': {'aliases': ['One', 'Two']}}
        result = make_aliases(data)
        self.assertEqual(result, [{'auctions.rubble.financial': ['One', 'Two']}])

    def test_make_bad_alias(self):
        result = make_aliases(None)
        self.assertEqual(result, [])

    def test_generate_id(self):
        id = generate_id()

        self.assertEqual(len(id), 32)
        self.assertEqual(type(UUID(id)), UUID)

    def test_get_file_path(self):
        here = '/absolute/path/app/'
        need_file = 'need_file'
        path = get_file_path(here, need_file)
        self.assertEqual(path, '/absolute/path/app/need_file')

        need_file = '/absolute/path/need_file'
        path = get_file_path(here, need_file)
        self.assertEqual(path, '/absolute/path/need_file')

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

    @mock.patch('openprocurement.api.utils.common.generate_id')
    def test_set_ownership(self, mock_generate_id):
        request = mock.MagicMock()
        mock_generate_id.return_value = '1234567890abcdef1234567890abcdef'
        # '0f20c55ac78f7336576260487b865a89a72b396d761ac69d00902cf5bd021d1c51b17191098dc9626f4582ab125efd9053fff1c8b58782e2fe70f7cb4b7bd7ee'

        item = self.OwnershipTestItem()
        expected_result = {'token': '1234567890abcdef1234567890abcdef', 'transfer': '1234567890abcdef1234567890abcdef'}

        result = set_ownership(item, request)
        self.assertEqual(result, expected_result)
        self.assertEqual(item.owner_token, expected_result['token'])
        self.assertEqual(item.transfer_token, sha512(expected_result['token']).hexdigest())

    @mock.patch('openprocurement.api.utils.common.generate_id')
    def test_set_ownership_with_passed_transfer_token(self, mock_generate_id):
        request = mock.MagicMock()
        mock_generate_id.return_value = '1234567890abcdef1234567890abcdef'
        request.authenticated_userid = 'concierge'
        request.json_body = {'data': {'transfer_token': 'test_transfer_token'}}

        item = self.OwnershipTestItem()
        expected_result = {'token': '1234567890abcdef1234567890abcdef'}
        result = set_ownership(item, request)
        self.assertEqual(result, expected_result)
        self.assertEqual(item.owner_token, expected_result['token'])
        self.assertEqual(item.transfer_token, 'test_transfer_token')

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

    def test_connection_mock_config(self):
        def check_nested_key(res, connector):
            for connect in connector:
                self.assertIn(connect, res.keys())
                res = res[connect]

        base = {"one": 1, "two": 2}
        part = {"three": 3}
        res = connection_mock_config(part, base=base)
        self.assertIn(part.keys()[0], res.keys())


        base = {"one": 1, "two": 2}
        part = {"three": 3}

        connector = ('level0', 'level1')
        res = connection_mock_config(part, connector=connector, base=base)
        check_nested_key(res, connector)

        connector = ('level0',)
        res = connection_mock_config(part, connector=connector, base=base)
        check_nested_key(res, connector)

        base = {
            "level0":{
                "level1": 2,
                "need":"info"
            },
            "data": "good"
        }
        part = {"three": 3}

        connector = ('level0', 'level1')
        res = connection_mock_config(part, connector=connector, base=base)
        check_nested_key(res, connector)

        connector = ('level0',)
        res = connection_mock_config(part, connector=connector, base=base)
        check_nested_key(res, connector)


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


def auction_mock(procurementMethodDetails):
    """Returns auction mock for accelerated mode testing.
    """
    auction = mock.MagicMock()
    acceleration_field = {'procurementMethodDetails': procurementMethodDetails}

    auction.__getitem__.side_effect = acceleration_field.__getitem__
    auction.__iter__.side_effect = acceleration_field.__iter__
    auction.__contains__.side_effect = acceleration_field.__contains__

    return auction


class CalculateBusinessDateTestCase(unittest.TestCase):

    def test_accelerated_calculation(self):
        # auction = auction_mock(procurementMethodDetails='quick, accelerator=1440') # TODO: Fix mocked attr
        auction = {"procurementMethodDetails": 'quick, accelerator=1440'}
        start = get_now()
        period_to_add = timedelta(days=1440)
        result = calculate_business_date(start, period_to_add, auction)
        self.assertEqual((result - start).days, 1)

    def test_accelerated_calculation_specific_hour(self):
        # auction = auction_mock(procurementMethodDetails='quick, accelerator=1440') # TODO: Fix mocked attr
        auction = {"procurementMethodDetails": 'quick, accelerator=1440'}
        start = datetime(2018, 4, 2, 16)
        specific_hour = start.hour + 2
        period_to_add = timedelta(days=20)
        result = calculate_business_date(start, period_to_add, auction, specific_hour=specific_hour)
        target_seconds = 20*60+5
        self.assertEqual((result - start).seconds, target_seconds)

    def test_accelerated_calculation_specific_time(self):
        auction = {"procurementMethodDetails": 'quick, accelerator=1440'}
        start = datetime(2018, 4, 2, 16)
        specific_time = time(18, 30)
        period_to_add = timedelta(days=20)
        result = calculate_business_date(start, period_to_add, auction, specific_time=specific_time)
        target_seconds = 20*60+6
        self.assertEqual((result - start).seconds, target_seconds)

    def test_common_calculation_with_working_days(self):
        """This test assumes that <Mon 2018-4-9> is holiday, besides regular holidays
        of that month. It must be fixed in `working_days.json` file, that translates
        into `WORKING_DAYS` constant.
        """
        start = datetime(2018, 4, 2)
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17)
        result = calculate_business_date(start, business_days_to_add, None, working_days=True)

        self.assertEqual(result, target_end_of_period)

    def test_common_calculation_with_working_days_working_end(self):
        start = datetime(2018, 10, 11)
        business_days_to_add = timedelta(days=3)
        target_end_of_period = datetime(2018, 10, 17)
        result = calculate_business_date(start, business_days_to_add, None, working_days=True)

        self.assertEqual(result, target_end_of_period)

    def test_common_calculation_with_working_days_specific_hour(self):
        """This test assumes that <Mon 2018-4-9> is holiday, besides regular holidays
        of that month. It must be fixed in `working_days.json` file, that translates
        into `WORKING_DAYS` constant.
        """
        start = datetime(2018, 4, 2)
        specific_hour = 18
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17)
        result = calculate_business_date(
            start, business_days_to_add, None, working_days=True, specific_hour=specific_hour
        )

        self.assertEqual(result, target_end_of_period + timedelta(hours=specific_hour))

    def test_calculate_with_negative_time_period(self):
        start = datetime(2018, 4, 17)
        business_days_to_add = timedelta(days=-10)
        target_end_of_period = datetime(2018, 4, 2)
        result = calculate_business_date(start, business_days_to_add, None, working_days=True)

        self.assertEqual(result, target_end_of_period)

    def test_start_is_holiday_specific_hour_none(self):
        start = datetime(2000, 5, 6, 13, 22)  # Saturday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 9, 0, 0)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_start_is_holiday_specific_hour_set(self):
        start = datetime(2000, 5, 6, 20, 22)  # Saturday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 8, 18, 0)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=18)

        self.assertEqual(result, target_end)

    def test_start_is_holiday_specific_hour_set_with_tz(self):
        TARGET_HOUR = 18

        tzone = timezone('Europe/Kiev')
        start = datetime(2018, 5, 6, 20, 22, tzinfo=tzone)  # Saturday
        days_to_add = timedelta(days=1)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=TARGET_HOUR)

        self.assertEqual(result.hour, TARGET_HOUR)

    def test_start_is_not_holiday_specific_hour_none(self):
        start = datetime(2000, 5, 5, 20, 22)  # Friday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 8, 20, 22)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_start_is_not_holiday_specific_hour_set(self):
        start = datetime(2000, 5, 5, 20, 22)  # Friday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 8, 18, 0)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=18)

        self.assertEqual(result, target_end)

    def test_reverse_start_is_not_holiday_specific_hour_not_set(self):
        start = datetime(2018, 7, 20, 17, 15)
        days_to_substract = timedelta(days=-4)
        target_end = datetime(2018, 7, 16, 17, 15)

        result = calculate_business_date(start, days_to_substract, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_reverse_start_is_not_holiday_specific_hour_not_set_one_day(self):
        start = datetime(2018, 7, 20)
        days_to_substract = timedelta(days=-1)
        target_end = datetime(2018, 7, 19)

        result = calculate_business_date(start, days_to_substract, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_start_is_not_holiday_specific_hour_not_set_one_day(self):
        start = datetime(2018, 7, 20)
        days_to_substract = timedelta(days=1)
        target_end = datetime(2018, 7, 23)

        result = calculate_business_date(start, days_to_substract, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_result_is_working_day(self):
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=3)
        target_end = datetime(2000, 5, 8)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_no_need_to_add_wd(self):
        """There isn't a need to add a working day if result is already working day"""
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=2)
        target_end = datetime(2000, 5, 5)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_unintended_jump(self):
        """Unintended holiday jump bug

        If timezone converting changes date, jumps when `result_is_working_day`==True`
        can overlap and cause error by adding wrong amount of days.
        """
        start = iso8601.parse_date('2018-12-19T00:00:00+02:00')
        days_to_add = timedelta(days=60)
        target_end = iso8601.parse_date('2019-02-18T18:00:00+02:00')

        result = calculate_business_date(start, days_to_add, None, specific_hour=18, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_with_specific_hour(self):
        start = datetime(2000, 5, 3, 15, 0)  # Wednesday
        days_to_add = timedelta(days=3)
        target_end = datetime(2000, 5, 8, 18, 0)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True, specific_hour=18)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_reverse(self):
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=-3)
        target_end = datetime(2000, 4, 28)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_timezone_aware(self):
        tzone = timezone('Europe/Kiev')
        start = tzone.localize(datetime(2018, 10, 20))
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)
        target_end = datetime(2018, 11, 9, 0, 0)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(str(start.utcoffset()), '3:00:00')
        self.assertEqual(str(result.utcoffset()), '2:00:00')


    def test_result_timezone_naive(self):
        start = datetime(2018, 10, 20)
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)
        target_end = datetime(2018, 11, 9, 0, 0)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertIsNone(start.utcoffset())
        self.assertIsNone(result.utcoffset())

    def test_date_add_days(self):
        start = datetime(2018, 10, 20).date()
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)
        target_end = date(2018, 11, 9)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)
        self.assertEqual(type(result), type(target_end))

    def test_kwargs(self):
        start = datetime(2018, 10, 20).date()
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)
        target_end = date(2018, 11, 9)

        result = calculate_business_date(
            start=start,
            delta=days_to_add,
            context=None,
            result_is_working_day=True
        )

        self.assertEqual(result, target_end)
        self.assertEqual(type(result), type(target_end))

    def test_zero_length_delta_working_days(self):
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=0)

        with self.assertRaises(ValueError) as exc:
            calculate_business_date(start, days_to_add, None, working_days=True, result_is_working_day=True)

    def test_common_calculation_with_working_days_specific_time(self):
        start = datetime(2018, 4, 2)
        specific_time = time(18, 4)
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17, 18, 4)
        result = calculate_business_date(
            start, business_days_to_add, None, working_days=True, specific_time=specific_time
        )

        self.assertEqual(result, target_end_of_period)

    def test_common_calculation_with_working_days_specific_time_priority(self):
        """Test `specific_time` kwarg priority over `specific_hour` one"""
        start = datetime(2018, 4, 2)
        specific_time = time(18, 4)
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17, 18, 4)
        result = calculate_business_date(
            start, business_days_to_add, None, working_days=True, specific_time=specific_time, specific_hour=18
        )

        self.assertEqual(result, target_end_of_period)


class CallBeforeTestCase(unittest.TestCase):

    class SomeClass(object):
        def __init__(self):
            self.run_first = False

        def want_run_first(self, *args, **kwargs):
            self.run_first = True

        @call_before(want_run_first)
        def some_method(self, param1, param2=None):
            pass

    def setUp(self):
        self.scarecrow = self.SomeClass()

    def test_ok(self):
        self.scarecrow.some_method('some_param', param2='i_am_here')
        self.assertTrue(self.scarecrow.run_first)


class TestSearchListWithDicts(unittest.TestCase):

    def setUp(self):
        self.container = (
            {
                'login': 'user1',
                'password': 'qwerty123',
            },
            {
                'login': 'user2',
                'password': 'abcd321',
                'other': 'I am User',
            }
        )

    def test_successful_search(self):
        result = search_list_with_dicts(self.container, 'login', 'user2')
        assert result['other'] == 'I am User'

    def test_unsuccessful_search(self):
        result = search_list_with_dicts(self.container, 'login', 'user3')
        assert result is None


class CreateAppMetaTestCase(unittest.TestCase):

    def setUp(self):
        self.temp_app_meta_path = dump_dict_to_tempfile(MOCK_CONFIG)

    def tearDown(self):
        os.unlink(self.temp_app_meta_path)

    def test_ok(self):
        app_meta = create_app_meta(self.temp_app_meta_path)
        root_keys = ('config', 'plugins', 'here')
        for k in root_keys:
            self.assertIn(k, app_meta.keys(), 'AppMeta was created without required base keys')


class RunMigrationsConsoleEntrypointTestCase(unittest.TestCase):

    @mock.patch('openprocurement.api.utils.common.run_migrations')
    @mock.patch('openprocurement.api.utils.common.create_app_meta')
    @mock.patch('openprocurement.api.utils.common.sys')
    def test_ok(self, argv_mock, create_app_meta, run_migrations):
        argv_mock.configure_mock(**{'argv': ('1', '2')})
        create_app_meta.return_value = 'test_app_meta'

        run_migrations_console_entrypoint()
        self.assertEqual(
            run_migrations.call_args[0][0], 'test_app_meta', 'run_migrations did not received proper argument'
        )


class PathToKvTestCase(unittest.TestCase):

    def setUp(self):
        self.testdict = {
            'forest': {
                'tree1': {
                    'leaf1': 'green',
                    'leaf2': 'brown'
                },
                'tree2': {
                    'leaf1': 'green',
                    'leaf2': 'brown',
                    'leaf3': 'green-brown'
                }
            }
        }

    def test_search_single_result(self):
        kv = ('leaf3', 'green-brown')
        target_r = (
            ('forest', 'tree2', 'leaf3'),
        )

        r = path_to_kv(kv, self.testdict)

        self.assertEqual(r, target_r)

    def test_search_multiple_results(self):
        kv = ('leaf1', 'green')
        target_r = (
            ('forest', 'tree1', 'leaf1'),
            ('forest', 'tree2', 'leaf1'),
        )

        r = path_to_kv(kv, self.testdict)

        self.assertEqual(r, target_r)

    def test_no_results(self):
        kv = ('root', 'no')
        target_r = None

        r = path_to_kv(kv, self.testdict)

        self.assertEqual(r, target_r)


class CollectPackagesForMigrationTestCase(unittest.TestCase):

    def setUp(self):
        self.plugins = deepcopy(RANDOM_PLUGINS)

    def test_ok(self):
        result = collect_packages_for_migration(self.plugins)

        target_result = ('auctions.rubble.other',)
        self.assertEqual(result, target_result)

    def test_none_find(self):
        self.plugins['api']['plugins']['auctions.core']['plugins']['auctions.rubble.other']['migration'] = False

        result = collect_packages_for_migration(self.plugins)

        target_result = None
        self.assertEqual(result, target_result)


class RoundSecondsToHoursTestCase(unittest.TestCase):

    def test_round_down(self):
        seconds = 18010.0  # 5 hours 10 seconds
        hours = 5
        res = round_seconds_to_hours(seconds)

        self.assertEqual(hours, res)

    def test_round_up(self):
        seconds = 17099  # 4 hours 59 seconds
        hours = 5
        res = round_seconds_to_hours(seconds)

        self.assertEqual(hours, res)

    def test_seconds_are_aliquot_to_hours(self):
        seconds = 18000  # 4 hours 59 seconds
        hours = 5
        res = round_seconds_to_hours(seconds)

        self.assertEqual(hours, res)


class SetTimezoneTestCase(unittest.TestCase):

    def test_only_timezone_has_changed(self):
        kyiv_tz = timezone('Europe/Kiev')
        d_in = datetime.now(kyiv_tz)
        res = set_timezone(d_in, utc)
        self.assertEqual(d_in.hour, res.hour)
        self.assertNotEqual(res.tzinfo, None, 'tzinfo must be present')


class UtcoffsetIsAliquotToHoursTestCase(unittest.TestCase):

    def test_is_not_aliquot(self):
        dt = iso8601.parse_date('2018-12-21T13:11:36+05:03')

        res = utcoffset_is_aliquot_to_hours(dt)

        self.assertEqual(res, False, 'offset is not aliquot to hours')

    def test_is_aliquot(self):
        dt = iso8601.parse_date('2018-12-21T13:11:36+05:00')

        res = utcoffset_is_aliquot_to_hours(dt)

        self.assertTrue(res, 'offset is aliquot to hours')


class UtcoffsetDifferenceTestCase(unittest.TestCase):

    def test_difference_is_present(self):
        tstamp = '2018-12-22T15:49:17.787628+03:00'
        dt = iso8601.parse_date(tstamp)
        target_res = (1, 2)

        res = utcoffset_difference(dt)

        self.assertEqual(res, target_res)

    def test_difference_is_none(self):
        tstamp = '2018-12-22T15:49:17.787628+02:00'
        dt = iso8601.parse_date(tstamp)
        target_res = (0, 2)

        res = utcoffset_difference(dt)

        self.assertEqual(res, target_res)

    def test_difference_is_present_and_negative(self):
        tstamp = '2018-12-22T15:49:17.787628+01:00'
        dt = iso8601.parse_date(tstamp)
        target_res = (-1, 2)

        res = utcoffset_difference(dt)

        self.assertEqual(res, target_res)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UtilsTest))
    suite.addTest(unittest.makeSuite(CalculateBusinessDateTestCase))
    suite.addTest(unittest.makeSuite(CallBeforeTestCase))
    suite.addTest(unittest.makeSuite(TestSearchListWithDicts))
    suite.addTest(unittest.makeSuite(CreateAppMetaTestCase))
    suite.addTest(unittest.makeSuite(RunMigrationsConsoleEntrypointTestCase))
    suite.addTest(unittest.makeSuite(PathToKvTestCase))
    suite.addTest(unittest.makeSuite(CollectPackagesForMigrationTestCase))
    suite.addTest(unittest.makeSuite(RoundSecondsToHoursTestCase))
    suite.addTest(unittest.makeSuite(SetTimezoneTestCase))
    suite.addTest(unittest.makeSuite(UtcoffsetIsAliquotToHoursTestCase))
    suite.addTest(unittest.makeSuite(UtcoffsetDifferenceTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
