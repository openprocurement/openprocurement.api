# -*- coding: utf-8 -*-
class LoggingContext(object):
    """Container for the logging data, that must evolve during the request lifecycle"""

    def __init__(self, context=None):
        self._context = context if context else {}

    def get_context(self):
        return self._context

    def get_item(self, key):
        return self._context.get(key)

    def set_item(self, key, value):
        upper_key = key.upper()
        self._context[upper_key] = value

    def set_items(self, items):
        for k, v in items.items():
            self.set_context_item(k, v)

    def to_journal_logging_context(self, message=None):
        """Convert to JournalLoggingContext object"""

        journal_context = JournalLoggingContext()
        message = message if message else {}

        for k, v in self._context.items():
            journal_context.set_item(k, v)

        for k, v in message.items():
            journal_context.set_item(k, v, add_prefix=False)  # message must be added with key unprefixed

        return journal_context


class JournalLoggingContext(LoggingContext):

    _JOURNAL_CONTEXT_KEY_PREFIX = 'JOURNAL_'

    def set_item(self, key, value, add_prefix=True):
        if not key.startswith(self._JOURNAL_CONTEXT_KEY_PREFIX):
            j_key = self._JOURNAL_CONTEXT_KEY_PREFIX + key.upper()
            self._context[j_key] = value
