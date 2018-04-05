# -*- coding: utf-8 -*-
from uuid import uuid4
from copy import deepcopy

from schematics.types import (
    StringType,
    URLType,
    BaseType,
    IntType
)
from schematics.exceptions import ValidationError
from schematics.types.compound import ModelType, ListType

from openprocurement.api.models.schematics_extender import DecimalType
from openprocurement.api.constants import (
    DEFAULT_ITEM_CLASSIFICATION,
    ITEM_CLASSIFICATIONS,
    DOCUMENT_TYPES,
)
from openprocurement.api.models.registry_models.roles import item_roles

from openprocurement.api.models.schematics_extender import (
    Model,
    IsoDateTimeType,
)
from openprocurement.api.models.registry_models.ocds import (
    ItemClassification,
    Identifier,
    Item as BaseItem,
    Document as BaseDocument,
    BaseUnit,
    Address,
    Organization,
    ContactPoint
)

class RegistrationDetails(Model):
    status = StringType(choices=['unknown', 'proceed', 'complete'], required=True)
    registrationID = StringType()
    registrationDate = IsoDateTimeType()

    def validate_registrationID(self, data, value):
        if value and data['status'] != 'complete':
            raise ValidationError(u"You can fill registrationID only when status is complete")

    def validate_registrationDate(self, data, value):
        if value and data['status'] != 'complete':
            raise ValidationError(u"You can fill registrationDate only when status is complete")


LOKI_ITEM_CLASSIFICATIONS = deepcopy(ITEM_CLASSIFICATIONS)
LOKI_ITEM_CLASSIFICATIONS.update({'UA-EDR': []})


class UAEDRItemClassification(ItemClassification):
    scheme = StringType(required=True, default=DEFAULT_ITEM_CLASSIFICATION, choices=LOKI_ITEM_CLASSIFICATIONS.keys())

    def validate_id(self, data, code):
        if data.get('scheme') == 'UA-EDR':
            return
        available_codes = LOKI_ITEM_CLASSIFICATIONS.get(data.get('scheme'), [])
        if code not in available_codes:
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(available_codes)))


class Item(BaseItem):
    class Options:
        roles = item_roles

    unit = ModelType(BaseUnit, required=True)
    quantity = DecimalType(precision=-4, required=True)
    address = ModelType(Address, required=True)
    classification = ModelType(ItemClassification, required=True)
    additionalClassifications = ListType(ModelType(UAEDRItemClassification), default=list())
    registrationDetails = ModelType(RegistrationDetails, required=True)

    def validate_schema_properties(self, data, new_schema_properties):
        if new_schema_properties:
            raise ValidationError('Opportunity to use schema_properties is disabled')


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
LOKI_DOCUMENT_TYPES += ['x_dgfAssetFamiliarization', 'procurementPlan', 'projectPlan', 'cancellationDetails']


class Document(BaseDocument):
    documentOf = StringType(choices=['lot', 'item'])
    documentType = StringType(choices=LOKI_DOCUMENT_TYPES)
    index = IntType(required=False)
    accessDetails = StringType()

    def validate_accessDetails(self, data, value):
        if value is None and data['documentType'] == 'x_dgfAssetFamiliarization':
            raise ValidationError(u"accessDetails is required, when documentType is x_dgfAssetFamiliarization")


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
