# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.configurator import Configurator, ConfiguratorException


class ConfiguratorTest(unittest.TestCase):

    def test_configurator(self):
        test_configs = {}
        conf = Configurator(test_configs, {})
        self.assertEqual(conf.AUCTION_PREFIX, Configurator.fields['AUCTION_PREFIX']['default'])

        test_configs = {'AUCTION_PREFIX': 1}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs, {})
        self.assertEqual(
            'AUCTION_PREFIX should be str type',
            exc.exception.message
        )

        test_configs = {'AUCTION_PREFIX': 'AU-EU'}
        conf = Configurator(test_configs, {})
        with self.assertRaises(ConfiguratorException) as exc:
            conf.AUCTION_PREFIX = 'AU-PS'
        self.assertEqual(
            'You can\'t change configurator after it was instantiated.',
            exc.exception.message
        )

        test_configs = {'AUCTION_PREFIX': 'AU-EU', 'justField': 'field'}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs, {})
        self.assertEqual(
            Configurator.error_messages['fields'],
            exc.exception.message
        )

        def f(self):
            pass
        functions = {'f': f}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator({}, functions)
        self.assertEqual(
            Configurator.error_messages['functions'],
            exc.exception.message
        )

        def test():
            pass
        Configurator.functions = {'test': {'default': f}}

        with self.assertRaises(ConfiguratorException) as exc:
            Configurator({}, {'test': test})
        self.assertEqual(
            Configurator.error_messages['function_params'],
            exc.exception.message
        )

        with self.assertRaises(ConfiguratorException) as exc:
            Configurator({}, {'test': 1})
        self.assertEqual(
            Configurator.error_messages['type_error'].format('Functions', 'function'),
            exc.exception.message
        )

        conf = Configurator({}, {})
        self.assertEqual(conf.test.__name__, f.__name__)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(ConfiguratorTest))
    return tests
