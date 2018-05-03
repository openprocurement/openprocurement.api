from copy import deepcopy

from schematics.exceptions import ValidationError
from schematics.types import StringType, BaseType, URLType, IntType
from schematics.types.compound import ModelType, ListType

from openprocurement.api.constants import (
    DOCUMENT_TYPES, DEFAULT_LOKI_ITEM_CLASSIFICATION, LOKI_ITEM_CLASSIFICATION, LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS
)
from openprocurement.api.models.common import ContactPoint, BaseUnit, Address
from openprocurement.api.models.ocds import (
    ItemClassification, BaseItem, Identifier, BaseDocument, Organization
)
from openprocurement.api.models.roles import item_roles
from openprocurement.api.models.schematics_extender import Model, IsoDateTimeType, DecimalType


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
    scheme = StringType(
        required=True, default=DEFAULT_LOKI_ITEM_CLASSIFICATION, choices=LOKI_ITEM_CLASSIFICATION.keys()
    )

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
