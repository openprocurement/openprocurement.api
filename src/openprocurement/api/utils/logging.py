# -*- coding: utf-8 -*-
class LoggingContext(object):

    _JOURNAL_CONTEXT_KEY_PREFIX = 'JOURNAL_'

    def __init__(self, context=None):
        self._context = context if context else {}

    def __iter__(self):
        return self

    def next(self):
        for k in self._context:
            yield (k, self._context[k])

    def get_context(self):
        return self._context

    def get_context_item(self, key):
        return self._context.get(key)

    def set_context_item(self, key, value):
        upper_key = key.upper()
        self._context[upper_key] = value

    def set_context_items(self, items):
        for k, v in items.items():
            self.set_context_item(k, v)

    def to_journal_context(self, message):
        journal_context = {}

        for k, v in self:
            journal_key = self._JOURNAL_CONTEXT_KEY_PREFIX + k
            journal_context[journal_key] = v

        journal_context.update(message)  # message must be added with key unprefixed

        return journal_context
