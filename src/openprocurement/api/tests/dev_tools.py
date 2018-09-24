# -*- coding: utf-8 -*-
import os
import sys
import unittest

from isodate import strftime
from isodate.duration import Duration
from schematics.transforms import whitelist
from schematics.types import BooleanType, StringType
from schematics.types.serializable import serializable
from openprocurement.api.roles import RolesFromCsv
from openprocurement.api.tests.base import BaseWebTest
from openprocurement.api.models import Model, IsoDurationType
from openprocurement.api.dev_tools import (
    create_csv_roles,
    get_fields_name,
    get_roles_from_object
)


class TestModel(Model):
    test_field0 = BooleanType()
    test_field1 = StringType()
    test_field2 = StringType()

    @serializable(serialized_name="status")
    def serialize_status(self):
        return 'test_status'


class CreateRoleCsvTest(BaseWebTest):

    def test_fields(self):
        fields = get_fields_name(TestModel)
        list_fields = list(fields)
        self.assertEqual(len(fields), 5)
        self.assertEqual(list_fields[0], 'test_field0')
        self.assertEqual(list_fields[1], 'test_field1')
        self.assertEqual(list_fields[2], 'test_field2')
        self.assertEqual(list_fields[3], '__parent__')
        self.assertEqual(list_fields[4], 'serialize_status')

    def test_get_roles(self):
        roles = get_roles_from_object(TestModel)
        fields = ['test_field0', 'test_field1', 'test_field2', 'serialize_status']
        self.assertEqual(len(roles), 2)
        self.assertEqual(roles.keys()[0], 'default')
        self.assertEqual(roles.keys()[1], 'embedded')
        self.assertEqual(roles[roles.keys()[0]], set(fields))
        self.assertEqual(roles[roles.keys()[1]], set(fields))

    def test_create_role_csv(self):
        create_csv_roles(TestModel)
        roles = RolesFromCsv('{0}.csv'.format(TestModel.__name__), relative_to=__file__)
        path_role_csv = ''
        for i in os.path.abspath(sys.modules[TestModel.__module__].__file__).split('/')[:-1]:
            path_role_csv += i + '/'
        white_list_roles = whitelist('test_field0', 'test_field1', 'test_field2', 'serialize_status')
        self.assertEqual(len(roles), 2)
        self.assertEqual(roles.keys()[0], 'default')
        self.assertEqual(roles.keys()[1], 'embedded')
        for i in roles.keys():
            self.assertEqual(roles[i], white_list_roles)
        os.remove('{0}.csv'.format(path_role_csv + TestModel.__name__))


class IsoDurationTypeTest(BaseWebTest):

    def test_iso_duration_type(self):
        type_duration = IsoDurationType()
        period_str = 'P3Y6M4DT12H30M5S'
        duration_period = Duration(years=3, months=6, days=4, hours=12, minutes=30, seconds=5)
        res_to_native = type_duration.to_native(period_str)

        self.assertEqual(res_to_native.years, 3)
        self.assertEqual(res_to_native.months, 6)
        self.assertEqual(res_to_native.days, 4)
        self.assertEqual(res_to_native.seconds, 45005)
        self.assertEqual(res_to_native, duration_period)
        self.assertEqual(strftime(res_to_native, "P%P"), period_str)

        res_to_primitive = type_duration.to_primitive(duration_period)
        self.assertEqual(res_to_primitive, period_str)
        # Parse with errors
        result = type_duration.to_native(duration_period)
        self.assertEqual(result, duration_period)
        with self.assertRaises(Exception) as context:
            result = type_duration.to_native('Ptest')
        self.assertEqual(context.exception.message,
                         ["ISO 8601 time designator 'T' missing. Unable to parse datetime string 'test'"])
        with self.assertRaises(Exception) as context:
            result = type_duration.to_native('P3Y6MW4DT12H30M5S')
        self.assertEqual(context.exception.message, ["Unrecognised ISO 8601 date format: '3Y6MW4D'"])
        with self.assertRaises(Exception) as context:
            result = type_duration.to_native(123123)
        self.assertEqual(context.exception.message,
                         [u'Could not parse 123123. Should be ISO8601 Durations.'])
        res_native1 = type_duration.to_native('P3Y6M4DT12H30M5S')
        res_native2 = type_duration.to_native('P2Y18M4DT12H30M5S')
        self.assertEqual(res_native1, res_native2)

        res_dur1 = type_duration.to_primitive(res_native1)
        res_dur2 = type_duration.to_primitive(res_native2)
        self.assertEqual('P3Y6M4DT12H30M5S', res_dur1)
        self.assertEqual('P2Y18M4DT12H30M5S', res_dur2)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CreateRoleCsvTest))
    suite.addTest(unittest.makeSuite(IsoDurationTypeTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
