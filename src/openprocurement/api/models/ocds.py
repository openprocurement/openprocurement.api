# -*- coding: utf-8 -*-
from uuid import uuid4

from schematics.types import (
    StringType,
    BooleanType,
    BaseType,
    MD5Type
)
from schematics.exceptions import ValidationError
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from zope.deprecation import deprecated

from openprocurement.api.constants import (
    DEFAULT_CURRENCY,
    DEFAULT_ITEM_CLASSIFICATION,
    ITEM_CLASSIFICATIONS,
    DOCUMENT_TYPES,
    IDENTIFIER_CODES,
    DEBTOR_TYPES
)
from openprocurement.api.models.common import (
    BaseUnit,
    BasicValue,
    Classification,
    Address,
    Location,
    BaseIdentifier,
    Organization as BaseOrganization
)
from openprocurement.api.models.roles import document_roles
from openprocurement.api.models.schematics_extender import (
    Model, DecimalType, IsoDateTimeType, HashType
)
from openprocurement.api.utils import get_now, serialize_document_url

from openprocurement.schemas.dgf.schemas_store import SchemaStore

from schematics_flexible.schematics_flexible import FlexibleModelType


# OCDS Building Blocks.
# More info: http://standard.open-contracting.org/latest/en/getting_started/building_blocks


class Value(BasicValue):
    valueAddedTaxIncluded = BooleanType(required=True, default=True)
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, default=DEFAULT_CURRENCY, max_length=3, min_length=3)


class ValueUAH(BasicValue):
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, choices=[u'UAH'], max_length=3, min_length=3)


class ItemClassification(Classification):
    scheme = StringType(required=True, default=DEFAULT_ITEM_CLASSIFICATION, choices=ITEM_CLASSIFICATIONS.keys())
    id = StringType(required=True)

    def validate_id(self, data, code):
        available_codes = ITEM_CLASSIFICATIONS.get(data.get('scheme'), [])
        if code not in available_codes:
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(available_codes)))


class Unit(BaseUnit):
    """
    Extends BaseUnit adding value field to it.
    """

    value = ModelType(Value)


class BaseDocument(Model):
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


BaseDocument.__name__ = 'Document'
Document = BaseDocument
deprecated('Document', 'Document is renamed to BaseDocument')


class Identifier(BaseIdentifier):
    # The scheme that holds the unique identifiers used to identify the item being identified.
    scheme = StringType(required=True, choices=IDENTIFIER_CODES)


class BaseItem(Model):
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


BaseItem.__name__ = 'Item'
Item = BaseItem
deprecated('Item', 'Item is renamed to BaseItem')


class Organization(BaseOrganization):
    identifier = ModelType(Identifier, required=True)
    additionalIdentifiers = ListType(ModelType(Identifier))


class Debt(Model):
    agreementNumber = StringType()
    debtorType = StringType(choices=DEBTOR_TYPES)
    dateSigned = IsoDateTimeType()
    value = ModelType(ValueUAH)
    debtCurrencyValue = ModelType(BasicValue)
