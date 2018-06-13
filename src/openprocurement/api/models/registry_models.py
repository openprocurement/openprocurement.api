from schematics.exceptions import ValidationError
from schematics.types import StringType, BaseType, IntType, URLType
from schematics.types.compound import ModelType, ListType

from openprocurement.api.constants import (
    DEFAULT_LOKI_ITEM_CLASSIFICATION,
    LOKI_ITEM_CLASSIFICATION,
    LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS,
    LOKI_DOCUMENT_TYPES,
    DOCUMENT_TYPE_OFFLINE,
    DOCUMENT_TYPE_URL_ONLY
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
        if code.find("00000-") > 0:
            raise ValidationError(
                'At least {} classification class (XXXX0000-Y) '
                'should be specified more precisely'.format(data.get('scheme'))
            )


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
    _document_types_offline = DOCUMENT_TYPE_OFFLINE
    _document_types_url_only = DOCUMENT_TYPE_URL_ONLY

    documentOf = StringType(choices=['lot', 'item'])
    documentType = StringType(choices=LOKI_DOCUMENT_TYPES, required=True)
    index = IntType(required=False)
    accessDetails = StringType()
    url = StringType()
    format = StringType(regex='^[-\w]+/[-\.\w\+]+$')

    def validate_hash(self, data, hash_):
        doc_type = data.get('documentType')
        doc_without_hash = self._document_types_url_only + self._document_types_offline
        if doc_type in doc_without_hash and hash_:
            raise ValidationError(u'This field is not required.')

    def validate_format(self, data, format_):
        doc_type = data.get('documentType')
        if doc_type in self._document_types_url_only and format_:
            raise ValidationError(u'This field is not required.')

    def validate_url(self, data, url):
        doc_type = data.get('documentType')
        if doc_type in self._document_types_offline and url:
            raise ValidationError(u'This field is not required.')
        if doc_type not in self._document_types_offline and not url:
            raise ValidationError(u'This field is required.')
        if doc_type in self._document_types_url_only:
            URLType().validate(url)

    def validate_accessDetails(self, data, accessDetails):
        if data.get('documentType') in self._document_types_offline and not accessDetails:
            raise ValidationError(u'This field is required.')


LokiDocument.__name__ = 'Document'


class AssetCustodian(Organization):
    name = StringType(required=True)
    kind = StringType(choices=['general', 'special', 'other'])


class AssetHolder(Organization):
    name = StringType(required=True)
    address = ModelType(Address)
    contactPoint = ModelType(ContactPoint)
    kind = StringType(choices=['general', 'special', 'other'])
