from schematics.exceptions import ValidationError
from schematics.types import StringType, BaseType, IntType
from schematics.types.compound import ModelType, ListType

from openprocurement.api.constants import (
    DEFAULT_LOKI_ITEM_CLASSIFICATION,
    LOKI_ITEM_CLASSIFICATION,
    LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS,
    LOKI_DOCUMENT_TYPES
)
from openprocurement.api.models.common import (
    ContactPoint, BaseUnit, Address, RegistrationDetails
)
from openprocurement.api.models.ocds import (
    ItemClassification, BaseItem, BaseDocument, Organization
)
from openprocurement.api.models.roles import item_roles
from openprocurement.api.models.schematics_extender import Model, IsoDateTimeType, DecimalType


# Loki models

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


class Decision(Model):
    title = StringType()
    title_ru = StringType()
    title_en = StringType()
    decisionDate = IsoDateTimeType(required=True)
    decisionID = StringType(required=True)
    decisionOf = StringType(choices=['lot', 'asset'])
    relatedItem = StringType()


class LokiDocument(BaseDocument):
    documentOf = StringType(choices=['lot', 'item'])
    documentType = StringType(choices=LOKI_DOCUMENT_TYPES, required=True)
    index = IntType(required=False)
    accessDetails = StringType()
    format = StringType(regex='^[-\w]+/[-\.\w\+]+$')

    def validate_accessDetails(self, data, value):
        if value is None and data['documentType'] == 'x_dgfAssetFamiliarization':
            raise ValidationError(u"accessDetails is required, when documentType is x_dgfAssetFamiliarization")


LokiDocument.__name__ = 'Document'


class AssetCustodian(Organization):
    name = StringType()
    kind = StringType(choices=['general', 'special', 'other'])


class AssetHolder(Organization):
    name = StringType()
    address = ModelType(Address)
    contactPoint = ModelType(ContactPoint)
    kind = StringType(choices=['general', 'special', 'other'])
