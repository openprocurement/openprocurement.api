# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.configurator import Configurator, ConfiguratorException


class ConfiguratorTest(unittest.TestCase):

    def test_configurator(self):
        test_configs = {'required_fields': []}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs)
        self.assertEqual(
            'You can\'t set this fields {}'.format(Configurator.not_allowed_fields),
            exc.exception.message
        )

        test_configs = {'not_allowed_fields': []}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs)
        self.assertEqual(
            'You can\'t set this fields {}'.format(Configurator.not_allowed_fields),
            exc.exception.message
        )

        test_configs = {'error_messages': []}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs)
        self.assertEqual(
            'You can\'t set this fields {}'.format(Configurator.not_allowed_fields),
            exc.exception.message
        )

        test_configs = {}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs)
        self.assertEqual(
            'This fields are required {}'.format(Configurator.required_fields.keys()),
            exc.exception.message
        )

        test_configs = {'AUCTION_PREFIX': 1}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs)
        self.assertEqual(
            'AUCTION_PREFIX should be str type',
            exc.exception.message
        )

        test_configs = {'AUCTION_PREFIX': 'AU-EU'}
        Configurator(test_configs)

        test_configs = {'AUCTION_PREFIX': 'AU-EU', 'justField': 'field'}
        conf = Configurator(test_configs)
        with self.assertRaises(ConfiguratorException) as exc:
            conf.AUCTION_PREFIX = 'AU-PS'
        self.assertEqual(
            'You can\'t change configurator after it was instantiated.',
            exc.exception.message
        )


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(ConfiguratorTest))
    return tests
