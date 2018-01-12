from unittest import TestCase

from openprocurement.api.constants import AWARDING_OF_PROCUREMENT_METHOD_TYPE
from openprocurement.api.utils import (
    get_awarding_type_by_procurement_method_type
)


class TestCoreUtils(TestCase):

    def test_get_awarding_type_by_procurement_method_type(self):
        for key in AWARDING_OF_PROCUREMENT_METHOD_TYPE.keys():
            awarding_type = get_awarding_type_by_procurement_method_type(key)
            self.assertEqual(
                awarding_type,
                AWARDING_OF_PROCUREMENT_METHOD_TYPE[key],
                'Awarding type was resolved wrong'
            )

    def test_get_awarding_type_by_procurement_method_type_raises(self):
        with self.assertRaises(ValueError) as context:
            get_awarding_type_by_procurement_method_type('jdfvhdlkjv')

