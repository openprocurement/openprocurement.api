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
            exc.exception.message,
            'AUCTION_PREFIX should be str type',
        )

        test_configs = {'AUCTION_PREFIX': 'AU-EU'}
        conf = Configurator(test_configs, {})
        with self.assertRaises(ConfiguratorException) as exc:
            conf.AUCTION_PREFIX = 'AU-PS'
        self.assertEqual(
            exc.exception.message,
            'You can\'t change configurator after it was instantiated.'
        )

        test_configs = {'AUCTION_PREFIX': 'AU-EU', 'justField': 'field'}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs, {})
        self.assertEqual(
            exc.exception.message,
            Configurator.error_messages['fields']
        )

        test_configs = {'fields': 'just some value'}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator(test_configs, {})
        self.assertEqual(
            exc.exception.message,
            Configurator.error_messages['standard_fields']
        )

        def f(self):
            pass
        functions = {'f': f}
        with self.assertRaises(ConfiguratorException) as exc:
            Configurator({}, functions)
        self.assertEqual(
            exc.exception.message,
            Configurator.error_messages['methods']
        )

        def test():
            pass
        Configurator.methods = {'test': {'default': f}}

        with self.assertRaises(ConfiguratorException) as exc:
            Configurator({}, {'test': test})
        self.assertEqual(
            exc.exception.message,
            Configurator.error_messages['method_params']
        )

        with self.assertRaises(ConfiguratorException) as exc:
            Configurator({}, {'test': 1})
        self.assertEqual(
            exc.exception.message,
            Configurator.error_messages['type_error'].format('Functions', 'function')
        )

        def bar(self):
            pass

        conf = Configurator({}, {'test': bar})
        self.assertEqual(conf.test.__name__, bar.__name__)

        conf = Configurator({}, {})
        self.assertEqual(conf.test.__name__, f.__name__)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(ConfiguratorTest))
    return tests
