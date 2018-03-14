# -*- coding: utf-8 -*-
from uuid import uuid4

from schematics.types import (StringType, FloatType, URLType, IntType,
                              BooleanType, BaseType, EmailType, MD5Type,
                              DecimalType as BaseDecimalType)
from schematics.exceptions import ValidationError, ConversionError
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics_flexible.schematics_flexible import FlexibleModelType

from openprocurement.schemas.dgf.schemas_store import SchemaStore

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from openprocurement.api.constants import (DEFAULT_CURRENCY,
    DEFAULT_ITEM_CLASSIFICATION, ITEM_CLASSIFICATIONS, DOCUMENT_TYPES,
    IDENTIFIER_CODES, DEBTOR_TYPES
)
from openprocurement.api.utils import get_now, serialize_document_url

from .schematics_extender import Model, IsoDateTimeType, HashType
from .roles import document_roles, organization_roles


# OCDS Building Blocks.
# More info: http://standard.open-contracting.org/latest/en/getting_started/building_blocks

class BasicValue(Model):
    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    currency = StringType(required=True, max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.


class Value(BasicValue):
    valueAddedTaxIncluded = BooleanType(required=True, default=True)
    currency = StringType(required=True, default=DEFAULT_CURRENCY, max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.


class ValueUAH(BasicValue):
    currency = StringType(required=True, choices=[u'UAH'], max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.


class Period(Model):
    startDate = IsoDateTimeType()  # The state date for the period.
    endDate = IsoDateTimeType()  # The end date for the period.

    def validate_startDate(self, data, value):
        if value and data.get('endDate') and data.get('endDate') < value:
            raise ValidationError(u"period should begin before its end")


class PeriodEndRequired(Period):
    endDate = IsoDateTimeType(required=True)  # The end date for the period.


class Classification(Model):
    scheme = StringType(required=True)  # The classification scheme for the goods
    id = StringType(required=True)  # The classification ID from the Scheme used
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    uri = URLType()


class ItemClassification(Classification):
    scheme = StringType(required=True, default=DEFAULT_ITEM_CLASSIFICATION, choices=ITEM_CLASSIFICATIONS.keys())
    id = StringType(required=True)

    def validate_id(self, data, code):
        available_codes = ITEM_CLASSIFICATIONS.get(data.get('scheme'), [])
        if code not in available_codes:
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(available_codes)))


class Unit(Model):
    """
    Description of the unit which the good comes in e.g. hours, kilograms.
    Made up of a unit name, and the value of a single unit.
    """

    name = StringType()
    name_en = StringType()
    name_ru = StringType()
    value = ModelType(Value)
    code = StringType(required=True)


class Address(Model):

    streetAddress = StringType()
    locality = StringType()
    region = StringType()
    postalCode = StringType()
    countryName = StringType(required=True)
    countryName_en = StringType()
    countryName_ru = StringType()


class Location(Model):
    latitude = BaseType(required=True)
    longitude = BaseType(required=True)
    elevation = BaseType()


class Document(Model):
    class Options:
        roles = document_roles

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    hash = HashType()
    documentOf = StringType(choices=['asset', 'lot'])
    documentType = StringType(choices=DOCUMENT_TYPES)
    title = StringType(required=True)  # A title of the document.
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # A description of the document.
    description_en = StringType()
    description_ru = StringType()
    format = StringType(required=True, regex='^[-\w]+/[-\.\w\+]+$')
    url = StringType(required=True)  # Link to the document or attachment.
    datePublished = IsoDateTimeType(default=get_now)
    dateModified = IsoDateTimeType(default=get_now)  # Date that the document was last dateModified
    language = StringType()
    relatedItem = MD5Type()
    author = StringType()

    @serializable(serialized_name="url")
    def download_url(self):
        return serialize_document_url(self)

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if data[k] == getattr(self, k)]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self


class Identifier(Model):
    scheme = StringType(required=True, choices=IDENTIFIER_CODES)  # The scheme that holds the unique identifiers used to identify the item being identified.
    id = BaseType(required=True)  # The identifier of the organization in the selected scheme.
    legalName = StringType()  # The legally registered name of the organization.
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # A URI to identify the organization.


class DecimalType(BaseDecimalType):

    def __init__(self, precision=-3, min_value=None, max_value=None, **kwargs):
        super(DecimalType, self).__init__(**kwargs)
        self.min_value, self.max_value = min_value, max_value
        self.precision = Decimal("1E{:d}".format(precision))

    def _apply_precision(self, value):
        try:
            value = Decimal(value).quantize(self.precision, rounding=ROUND_HALF_UP).normalize()
        except (TypeError, InvalidOperation):
            raise ConversionError(self.messages['number_coerce'].format(value))
        return value

    def to_primitive(self, value, context=None):
        return value

    def to_native(self, value, context=None):
        try:
            value = Decimal(value).quantize(self.precision, rounding=ROUND_HALF_UP).normalize()
        except (TypeError, InvalidOperation):
            raise ConversionError(self.messages['number_coerce'].format(value))

        if self.min_value is not None and value < self.min_value:
            raise ConversionError(self.messages['number_min'].format(value))
        if self.max_value is not None and self.max_value < value:
            raise ConversionError(self.messages['number_max'].format(value))

        return value


class Item(Model):
    """A good, service, or work to be contracted."""
    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    classification = ModelType(ItemClassification)
    additionalClassifications = ListType(ModelType(Classification), default=list())
    unit = ModelType(Unit)  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = DecimalType()  # The number of units required
    address = ModelType(Address)
    location = ModelType(Location)
    schema_properties = FlexibleModelType(SchemaStore())

    def validate_schema_properties(self, data, new_schema_properties):
        """ Raise validation error if code in schema_properties mismatch
            with classification id """
        if new_schema_properties and not data['classification']['id'].startswith(new_schema_properties['code']):
            raise ValidationError("classification id mismatch with schema_properties code")

class ContactPoint(Model):
    name = StringType(required=True)
    name_en = StringType()
    name_ru = StringType()
    email = EmailType()
    telephone = StringType()
    faxNumber = StringType()
    url = URLType()

    def validate_email(self, data, value):
        if not value and not data.get('telephone'):
            raise ValidationError(u"telephone or email should be present")


class Organization(Model):
    """An organization."""
    class Options:
        roles = organization_roles

    name = StringType(required=True)
    name_en = StringType()
    name_ru = StringType()
    identifier = ModelType(Identifier, required=True)
    additionalIdentifiers = ListType(ModelType(Identifier))
    address = ModelType(Address, required=True)
    contactPoint = ModelType(ContactPoint, required=True)


class Debt(Model):
    agreementNumber = StringType()
    debtorType = StringType(choices=DEBTOR_TYPES)
    dateSigned = IsoDateTimeType()
    value = ModelType(ValueUAH)
    debtCurrencyValue = ModelType(BasicValue)
