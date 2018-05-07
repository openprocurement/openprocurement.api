# -*- coding: utf-8 -*-

class ConfiguratorException(Exception):
    pass

configs = {
    'AUCTION_PREFIX': 'AU-EU'
}

class Configurator(object):
    required_fields = {
        'AUCTION_PREFIX': str
    }
    not_allowed_fields = ['required_fields', 'not_allowed_fields', 'error_messages']
    error_messages = {
        'required_fields': 'This fields are required {}',
        'type_error': '{} should be {} type',
        'not_allowed': 'You can\'t set this fields {}'.format(not_allowed_fields),
        'change_attr': 'You can\'t change configurator after it was instantiated.'
    }

    def __init__(self, config):
        if any(field in self.not_allowed_fields for field in config):
            raise ConfiguratorException(self.error_messages['not_allowed'])

        if not set(self.required_fields.keys()).issubset(set(config.keys())):
            raise ConfiguratorException(self.error_messages['required_fields'].format(self.required_fields.keys()))

        for field in self.required_fields:
            setattr(self, field, config[field])
        self.created = True

    def __setattr__(self, key, value):
        if getattr(self, 'created', False):
            raise ConfiguratorException(self.error_messages['change_attr'])
        if key in self.required_fields:
            if not isinstance(value, self.required_fields[key]):
                raise ConfiguratorException(
                    self.error_messages['type_error'].format(key, self.required_fields[key].__name__)
                )
        return super(Configurator, self).__setattr__(key, value)