# -*- coding: utf-8 -*-
from zope.deprecation import deprecated
from uuid import uuid4
from copy import deepcopy

from schematics.types import (
    StringType,
    FloatType,
    URLType,
    BooleanType,
    BaseType,
    EmailType,
    MD5Type,
    IntType
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
    IDENTIFIER_CODES,
    DEBTOR_TYPES,
    DEFAULT_LOKI_ITEM_CLASSIFICATION,
    LOKI_ITEM_CLASSIFICATION,
    LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS
)
from openprocurement.api.utils import get_now, serialize_document_url

from openprocurement.api.models.schematics_extender import (
    Model,
    IsoDateTimeType,
    HashType
)
from .roles import document_roles, organization_roles, item_roles


# OCDS Building Blocks.
# More info: http://standard.open-contracting.org/latest/en/getting_started/building_blocks

class BasicValue(Model):
    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    currency = StringType(required=True, max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.


class Value(BasicValue):
    valueAddedTaxIncluded = BooleanType(required=True, default=True)
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, default=DEFAULT_CURRENCY, max_length=3, min_length=3)


class ValueUAH(BasicValue):
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, choices=[u'UAH'], max_length=3, min_length=3)


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


class Identifier(Model):
    # The scheme that holds the unique identifiers used to identify the item being identified.
    scheme = StringType(required=True, choices=IDENTIFIER_CODES)
    id = BaseType(required=True)  # The identifier of the organization in the selected scheme.
    legalName = StringType()  # The legally registered name of the organization.
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # A URI to identify the organization.


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


# Loki models

class RegistrationDetails(Model):
    status = StringType(choices=['unknown', 'registering', 'complete'], required=True)
    registrationID = StringType()
    registrationDate = IsoDateTimeType()

    def validate_registrationID(self, data, value):
        if value and data['status'] != 'complete':
            raise ValidationError(u"You can fill registrationID only when status is complete")

    def validate_registrationDate(self, data, value):
        if value and data['status'] != 'complete':
            raise ValidationError(u"You can fill registrationDate only when status is complete")


class LokiItemClassification(ItemClassification):
    scheme = StringType(required=True, default=DEFAULT_LOKI_ITEM_CLASSIFICATION, choices=LOKI_ITEM_CLASSIFICATION.keys())

    def validate_id(self, data, code):
        available_codes = LOKI_ITEM_CLASSIFICATION.get(data.get('scheme'), [])
        if code not in available_codes:
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(available_codes)))


class UAEDRAndCadastralItemClassification(ItemClassification):
    scheme = StringType(required=True, default='UA-EDR', choices=LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS.keys())

    def validate_id(self, data, code):
        if data.get('scheme') in ['UA-EDR', 'cadastralNumber']:
            return
        available_codes = LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS.get(data.get('scheme'), [])
        if code not in available_codes:
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(available_codes)))


class LokiItem(BaseItem):
    class Options:
        roles = item_roles

    unit = ModelType(BaseUnit, required=True)
    quantity = DecimalType(precision=-4, required=True)
    address = ModelType(Address, required=True)
    classification = ModelType(LokiItemClassification, required=True)
    additionalClassifications = ListType(ModelType(UAEDRAndCadastralItemClassification), default=list())
    registrationDetails = ModelType(RegistrationDetails, required=True)

    def validate_schema_properties(self, data, new_schema_properties):
        if new_schema_properties:
            raise ValidationError('Opportunity to use schema_properties is disabled')


LokiItem.__name__ = 'Item'


class UAEDRIdentifier(Identifier):
    scheme = StringType(choices=['UA-EDR'])
    legalName = StringType(required=True)
    uri = URLType(required=True)


class Decision(Model):
    title = StringType()
    title_ru = StringType()
    title_en = StringType()
    decisionDate = IsoDateTimeType(required=True)
    decisionID = StringType(required=True)


LOKI_DOCUMENT_TYPES = deepcopy(DOCUMENT_TYPES)
LOKI_DOCUMENT_TYPES += [
    'x_dgfAssetFamiliarization', 'informationDetails', 'procurementPlan', 'projectPlan',
    'cancellationDetails'
]


class LokiDocument(BaseDocument):
    documentOf = StringType(choices=['lot', 'item'])
    documentType = StringType(choices=LOKI_DOCUMENT_TYPES)
    index = IntType(required=False)
    accessDetails = StringType()
    format = StringType(regex='^[-\w]+/[-\.\w\+]+$')

    def validate_accessDetails(self, data, value):
        if value is None and data['documentType'] == 'x_dgfAssetFamiliarization':
            raise ValidationError(u"accessDetails is required, when documentType is x_dgfAssetFamiliarization")


LokiDocument.__name__ = 'Document'


class AssetCustodian(Organization):
    name = StringType()
    identifier = ModelType(Identifier, serialize_when_none=False)
    additionalIdentifiers = ListType(ModelType(UAEDRIdentifier), default=list())
    address = ModelType(Address, serialize_when_none=False)
    contactPoint = ModelType(ContactPoint, serialize_when_none=False)
    kind = StringType(choices=['general', 'special', 'other'])


class AssetHolder(Model):
    name = StringType(required=True)
    name_ru = StringType()
    name_en = StringType()
    identifier = ModelType(UAEDRIdentifier, required=True)
    additionalIdentifiers = ListType(ModelType(UAEDRIdentifier), default=list())
    address = ModelType(Address)
    contactPoint = ModelType(ContactPoint)
