# -*- coding: utf-8 -*-
from types import FunctionType, MethodType
from inspect import getargspec


class ConfiguratorException(Exception):
    pass


configuration_info = {
    'AUCTION_PREFIX': 'AU-EU'
}


class Configurator(object):
    fields = {
        'AUCTION_PREFIX': {'type': str, 'default': 'AU-EU'}
    }
    functions = {}
    error_messages = {
        'fields': 'You can input only this fields {}'.format(fields.keys()),
        'type_error': '{} should be {} type',
        'change_attr': 'You can\'t change configurator after it was instantiated.',
        'functions': 'You can add only this functions {}'.format(functions.keys()),
        'function_params': 'All function must have at least one argument.'
    }

    def __init__(self, config, functions):
        if not all(field in self.fields for field in config):
            raise ConfiguratorException(self.error_messages['fields'])

        if not all(func in self.functions for func in functions):
            raise ConfiguratorException(self.error_messages['functions'])
        if not all(isinstance(func, FunctionType) for _, func in functions.items()):
            raise ConfiguratorException(self.error_messages['type_error'].format('Functions', 'function'))
        if not all(len(getargspec(func).args) > 0 for _, func in functions.items()):
            raise ConfiguratorException(self.error_messages['function_params'])

        for func in self.functions:
            method = MethodType(functions.get(func, self.functions[func]['default']), self)
            setattr(self, func, method)
        for field in self.fields:
            setattr(self, field, config.get(field, self.fields[field]['default']))
        self.created = True

    def __setattr__(self, key, value):
        if getattr(self, 'created', False):
            raise ConfiguratorException(self.error_messages['change_attr'])
        if key in self.fields:
            if not isinstance(value, self.fields[key]['type']):
                raise ConfiguratorException(
                    self.error_messages['type_error'].format(key, self.fields[key]['type'].__name__)
                )
        return super(Configurator, self).__setattr__(key, value)
