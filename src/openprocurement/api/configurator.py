# -*- coding: utf-8 -*-
from types import FunctionType, MethodType
from inspect import getargspec


class ConfiguratorException(Exception):
    pass


configuration_info = {
    'AUCTION_PREFIX': 'UA-EA'
}


class Configurator(object):
    """
    This class implements configurator logic which now is just a storage for constant and methods.
    To create instance you have to pass two arguments config and functions that described below.
    After instance was created you can`t change it in any way.
    In addition there is couple of class parameters that can`t be setted in any way they marked as immutable.

    :argument config:
        simple dict where key is a field that should be filled in configurator
        with value which is some constant.
    :argument functions:
        simple dict where key is a name of function that should be attached to
        instance of class and value is actually function that will be attached

    :param fields:
        dict where described what field with which type can be filled in configurator.
        :Example:

        {
            'NAME_OF_FIELD': {
                'type': str,
                'default': 'DEFAULT_VALUE'
            }
        }
        :param type: is one of builtins type(but in the future here can be a use defined types e.g. classes).
        :param default: just a default value that will be used if this field not found in config.
    :type fields: immutable dict

    :param methods:
        dict where described functions with which names can be attached to instance of class as method.
        :Example:

        {
            "method_name": {"default": default_function}
        }
        :param default: default function that will be turned into method after instance will be created
    :type methods: immutable dict

    :param error_messages: simple dict for getting error messages.
    :type error_messages: immutable dict
    """
    fields = {
        'AUCTION_PREFIX': {'type': str, 'default': 'UA-EA'},
        'ASSET_PREFIX': {'type': str, 'default': 'UA-AR-DGF'}
    }

    methods = {}
    standard_fields = ['fields', 'methods', 'immutable_fields', 'error_messages', 'created']
    error_messages = {
        'fields': 'You can input only this fields {}'.format(fields.keys()),
        'type_error': '{} should be {} type',
        'change_attr': 'You can\'t change configurator after it was instantiated.',
        'methods': 'You can add only this methods {}'.format(methods.keys()),
        'method_params': 'All methods must have at least one argument(self).',
        'standard_fields': 'This fields can\'t be changed in any way {}'.format(standard_fields)
    }

    def __init__(self, config, functions):
        # Check if there is no immutable_fields in config
        if any(field in self.standard_fields for field in config):
            raise ConfiguratorException(self.error_messages['standard_fields'])
        # Check if in config no extra fields comparing to `fields` param
        if not all(field in self.fields for field in config):
            raise ConfiguratorException(self.error_messages['fields'])

        # Check if in config no extra functions comparing to `methods` param
        if not all(func in self.methods for func in functions):
            raise ConfiguratorException(self.error_messages['methods'])
        # Check if in functions argument only objects with FunctionType, but no others callable.
        if not all(isinstance(func, FunctionType) for _, func in functions.items()):
            raise ConfiguratorException(self.error_messages['type_error'].format('Functions', 'function'))
        # Check if function has at least one argument which will be self.
        if not all(len(getargspec(func).args) > 0 for _, func in functions.items()):
            raise ConfiguratorException(self.error_messages['method_params'])

        # Turn functions to methods of Configurator instance
        for func in self.methods:
            method = MethodType(functions.get(func, self.methods[func]['default']), self)
            setattr(self, func, method)
        # Assign attributes from config to instance attributes
        for field in self.fields:
            setattr(self, field, config.get(field, self.fields[field]['default']))
        self.created = True

    def __setattr__(self, key, value):
        # Check if instance was created if it True than you can change nothing in instance of Configurator
        if getattr(self, 'created', False):
            raise ConfiguratorException(self.error_messages['change_attr'])
        # Check if type of attribute which set is equal to type described in `fields` param
        if key in self.fields:
            if not isinstance(value, self.fields[key]['type']):
                raise ConfiguratorException(
                    self.error_messages['type_error'].format(key, self.fields[key]['type'].__name__)
                )
        return super(Configurator, self).__setattr__(key, value)
