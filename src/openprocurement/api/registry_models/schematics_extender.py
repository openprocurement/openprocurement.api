# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from iso8601 import parse_date, ParseError
from isodate.duration import Duration
from isodate import parse_duration, ISO8601Error, duration_isoformat
from hashlib import algorithms, new as hash_new
from schematics.exceptions import ConversionError, ValidationError

from schematics.models import Model as SchematicsModel

from schematics.types.compound import ListType as BaseListType
from schematics.types import BaseType, StringType
from schematics.transforms import blacklist, export_loop, convert
from openprocurement.api.constants import TZ
from openprocurement.api.utils import set_parent


class IsoDateTimeType(BaseType):
    MESSAGES = {
        'parse': u'Could not parse {0}. Should be ISO8601.',
    }

    def to_native(self, value, context=None):
        if isinstance(value, datetime):
            return value
        try:
            date = parse_date(value, None)
            if not date.tzinfo:
                date = TZ.localize(date)
            return date
        except ParseError:
            raise ConversionError(self.messages['parse'].format(value))
        except OverflowError as e:
            raise ConversionError(e.message)

    def to_primitive(self, value, context=None):
        return value.isoformat()


class IsoDurationType(BaseType):
    MESSAGES = {
        'parse': u'Could not parse {0}. Should be ISO8601 duration format.',
    }

    def to_native(self, value, context=None):
        if isinstance(value, (timedelta, Duration)):
            return value
        try:
            return parse_duration(value)
        except (ISO8601Error, TypeError):
            raise ConversionError(self.messages['parse'].format(value))
        except OverflowError as e:
            raise ConversionError(e.message)

    def to_primitive(self, value, context=None):
        return duration_isoformat(value)


class HashType(StringType):

    MESSAGES = {
        'hash_invalid': "Hash type is not supported.",
        'hash_length': "Hash value is wrong length.",
        'hash_hex': "Hash value is not hexadecimal.",
    }

    def to_native(self, value, context=None):
        value = super(HashType, self).to_native(value, context)

        if ':' not in value:
            raise ValidationError(self.messages['hash_invalid'])

        hash_type, hash_value = value.split(':', 1)

        if hash_type not in algorithms:
            raise ValidationError(self.messages['hash_invalid'])

        if len(hash_value) != hash_new(hash_type).digest_size * 2:
            raise ValidationError(self.messages['hash_length'])
        try:
            int(hash_value, 16)
        except ValueError:
            raise ConversionError(self.messages['hash_hex'])
        return value


class ListType(BaseListType):

    def export_loop(self, list_instance, field_converter,
                    role=None, print_none=False):
        """Loops over each item in the model and applies either the field
        transform or the multitype transform.  Essentially functions the same
        as `transforms.export_loop`.
        """
        data = []
        for value in list_instance:
            if hasattr(self.field, 'export_loop'):
                shaped = self.field.export_loop(value, field_converter,
                                                role=role,
                                                print_none=print_none)
                feels_empty = shaped and len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            # Print if we want empty or found a value
            if feels_empty and self.field.allow_none():
                data.append(shaped)
            elif shaped is not None:
                data.append(shaped)
            elif print_none:
                data.append(shaped)

        # Return data if the list contains anything
        if len(data) > 0:
            return data
        elif len(data) == 0 and self.allow_none():
            return data
        elif print_none:
            return data


class Model(SchematicsModel):
    class Options(object):
        """Export options for Document."""
        serialize_when_none = False
        roles = {
            "default": blacklist("__parent__"),
            "embedded": blacklist("__parent__"),
        }

    __parent__ = BaseType()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for k in self._fields:
                if k != '__parent__' and self.get(k) != other.get(k):
                    return False
            return True
        return NotImplemented

    def convert(self, raw_data, **kw):
        """
        Converts the raw data into richer Python constructs according to the
        fields on the model
        """
        value = convert(self.__class__, raw_data, **kw)
        for i, j in value.items():
            if isinstance(j, list):
                for x in j:
                    set_parent(x, self)
            else:
                set_parent(j, self)
        return value

    def to_patch(self, role=None):
        """
        Return data as it would be validated. No filtering of output unless
        role is defined.
        """
        field_converter = lambda field, value: field.to_primitive(value)
        data = export_loop(self.__class__, self, field_converter, role=role, raise_error_on_role=True, print_none=True)
        return data

    def get_role(self):
        root = self.__parent__
        while root.__parent__ is not None:
            root = root.__parent__
        request = root.request
        return 'Administrator' if request.authenticated_role == 'Administrator' else 'edit'


class SifterListType(ListType):
    def __init__(self, field, min_size=None, max_size=None,
                 filter_by=None, filter_in_values=[], **kwargs):
        self.filter_by = filter_by
        self.filter_in_values = filter_in_values
        super(SifterListType, self).__init__(field, min_size=min_size,
                                             max_size=max_size, **kwargs)

    def export_loop(self, list_instance, field_converter,
                    role=None, print_none=False):
        """ Use the same functionality as original method but apply
        additional filters.
        """
        data = []
        for value in list_instance:
            if hasattr(self.field, 'export_loop'):
                item_role = role
                # apply filters
                if role not in ['plain', None] and self.filter_by and hasattr(value, self.filter_by):
                    val = getattr(value, self.filter_by)
                    if val in self.filter_in_values:
                        item_role = val

                shaped = self.field.export_loop(value, field_converter,
                                                role=item_role,
                                                print_none=print_none)
                feels_empty = shaped and len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            # Print if we want empty or found a value
            if feels_empty and self.field.allow_none():
                data.append(shaped)
            elif shaped is not None:
                data.append(shaped)
            elif print_none:
                data.append(shaped)

        # Return data if the list contains anything
        if len(data) > 0:
            return data
        elif len(data) == 0 and self.allow_none():
            return data
        elif print_none:
            return data