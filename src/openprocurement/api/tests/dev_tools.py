# -*- coding: utf-8 -*-
import os
import sys
import unittest
from schematics.transforms import whitelist
from schematics.types import BooleanType, StringType
from schematics.types.serializable import serializable
from openprocurement.api.roles import RolesFromCsv
from openprocurement.api.tests.base import BaseWebTest
from openprocurement.api.models import Model
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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CreateRoleCsvTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
