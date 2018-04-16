# -*- coding: utf-8 -*-
from uuid import uuid4

from schematics.types import (
    StringType,
    FloatType,
    BooleanType,
    BaseType,
    MD5Type,
)
from schematics.exceptions import ValidationError
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics_flexible.schematics_flexible import FlexibleModelType

from openprocurement.schemas.dgf.schemas_store import SchemaStore

from openprocurement.api.models.schematics_extender import DecimalType
from openprocurement.api.constants import (
    DEFAULT_CURRENCY,
    DEFAULT_ITEM_CLASSIFICATION,
    ITEM_CLASSIFICATIONS,
    DOCUMENT_TYPES,
    DEBTOR_TYPES
)
from openprocurement.api.utils import get_now, serialize_document_url
from openprocurement.api.models.models import (
    ContactPoint,
    Classification,
    Identifier,
    Address,
    Location
)
from openprocurement.api.models.schematics_extender import (
    Model,
    IsoDateTimeType,
    HashType
)
from .roles import document_roles, organization_roles


# OCDS Building Blocks.
# More info:
# http://standard.open-contracting.org/latest/en/getting_started/building_blocks

class BasicValue(Model):
    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, max_length=3, min_length=3)


class Value(BasicValue):
    valueAddedTaxIncluded = BooleanType(required=True, default=True)
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, default=DEFAULT_CURRENCY,
                          max_length=3, min_length=3)


class ValueUAH(BasicValue):
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, choices=[u'UAH'],
                          max_length=3, min_length=3)


class ItemClassification(Classification):
    scheme = StringType(required=True, default=DEFAULT_ITEM_CLASSIFICATION,
                        choices=ITEM_CLASSIFICATIONS.keys())
    id = StringType(required=True)

    def validate_id(self, data, code):
        available_codes = ITEM_CLASSIFICATIONS.get(data.get('scheme'), [])
        if code not in available_codes:
            raise ValidationError(
                BaseType.MESSAGES['choices'].format(unicode(available_codes)))


class BaseUnit(Model):
    """
    Description of the unit which the good comes in e.g. hours, kilograms.
    Made up of a unit name of a single unit.
    """

    name = StringType()
    name_en = StringType()
    name_ru = StringType()
    code = StringType(required=True)


class Unit(BaseUnit):
    """
    Extends BaseUnit adding value field to it.
    """

    value = ModelType(Value)


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
    # Date that the document was last dateModified
    dateModified = IsoDateTimeType(default=get_now)
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


class Item(Model):
    """A good, service, or work to be contracted."""
    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    # A description of the goods, services to be provided.
    description = StringType(required=True)
    description_en = StringType()
    description_ru = StringType()
    classification = ModelType(ItemClassification)
    additionalClassifications = ListType(
        ModelType(Classification), default=list())
    # Description of the unit which the good comes in e.g. hours, kilograms
    unit = ModelType(Unit)
    quantity = DecimalType()  # The number of units required
    address = ModelType(Address)
    location = ModelType(Location)
    schema_properties = FlexibleModelType(SchemaStore())

    def validate_schema_properties(self, data, new_schema_properties):
        """ Raise validation error if code in schema_properties mismatch
            with classification id """
        mismatch = not data['classification']['id']\
            .startswith(new_schema_properties['code'])
        if new_schema_properties and mismatch:
            raise ValidationError(
                "classification id mismatch with schema_properties code")


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
