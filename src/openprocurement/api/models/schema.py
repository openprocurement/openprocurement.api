# -*- coding: utf-8 -*-
from uuid import uuid4

from couchdb_schematics.document import SchematicsDocument
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist, export_loop
from schematics.types import (
    BaseType,
    BooleanType,
    FloatType,
    IntType,
    MD5Type,
    StringType,
    URLType,
)
from schematics.types.compound import (
    DictType,
    ModelType,
)
from schematics.types.serializable import serializable

from openprocurement.api.constants import (
    CPV_BLOCK_FROM,
    CPV_CODES,
    DEFAULT_CURRENCY,
    DEFAULT_LOKI_ITEM_CLASSIFICATION,
    DOCUMENT_TYPE_OFFLINE,
    DOCUMENT_TYPE_URL_ONLY,
    LOKI_DOCUMENT_TYPES,
    LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS,
    LOKI_ITEM_CLASSIFICATION,
    ORA_CODES,
    ORA_CODES_AUCTIONS,
)
from openprocurement.api.models.common import (
    Address,
    BaseIdentifier,
    BaseUnit,
    BasicValue,
    Classification,
    ContactPoint,
    Location,
    Organization as BaseOrganization,
    Period,
    RegistrationDetails,
)
from openprocurement.api.models.ocds import (
    ItemClassification,
    BaseItem,
    BaseDocument,
    Organization as ocds_organization,
)
from openprocurement.api.models.schematics_extender import (
    HashType,
    IsoDateTimeType,
    ListType,
    Model,
    DecimalType,
)
from openprocurement.api.utils import (
    get_document_creation_date,
    get_now,
    get_schematics_document,
    serialize_document_url,
)
from openprocurement.api.validation import (
    atc_inn_validator,
    cpv_validator,
    validate_uniq,
)
from openprocurement.api.models.roles import item_roles


schematics_default_role = SchematicsDocument.Options.roles['default'] + blacklist("__parent__")
schematics_embedded_role = SchematicsDocument.Options.roles['embedded'] + blacklist("__parent__")


class Value(BasicValue):
    valueAddedTaxIncluded = BooleanType(required=True, default=True)
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, default=DEFAULT_CURRENCY, max_length=3, min_length=3)


class FeatureValue(Model):

    value = FloatType(required=True, min_value=0.0, max_value=0.3)
    title = StringType(required=True, min_length=1)
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()


def validate_values_uniq(values, *args):
    codes = [i.value for i in values]
    if any([codes.count(i) > 1 for i in set(codes)]):
        raise ValidationError(u"Feature value should be uniq for feature")


class Feature(Model):

    code = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    featureOf = StringType(required=True, choices=['tenderer', 'lot', 'item'], default='tenderer')
    relatedItem = StringType(min_length=1)
    title = StringType(required=True, min_length=1)
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    enum = ListType(ModelType(FeatureValue), default=list(), min_size=1, validators=[validate_values_uniq])

    def validate_relatedItem(self, data, relatedItem):
        if not relatedItem and data.get('featureOf') in ['item', 'lot']:
            raise ValidationError(u'This field is required.')
        if (
            data.get('featureOf') == 'item'
            and isinstance(data['__parent__'], Model)
            and relatedItem
            not in [i.id for i in data['__parent__'].items]
        ):
            raise ValidationError(u"relatedItem should be one of items")
        if (
            data.get('featureOf') == 'lot'
            and isinstance(data['__parent__'], Model)
            and relatedItem
            not in [i.id for i in data['__parent__'].lots]
        ):
            raise ValidationError(u"relatedItem should be one of lots")


class ComplaintModelType(ModelType):
    view_claim_statuses = ['active.enquiries', 'active.tendering', 'active.auction']

    def export_loop(self, model_instance, field_converter,
                    role=None, print_none=False):
        """
        Calls the main `export_loop` implementation because they are both
        supposed to operate on models.
        """
        if isinstance(model_instance, self.model_class):
            model_class = model_instance.__class__
        else:
            model_class = self.model_class

        if role in self.view_claim_statuses and getattr(model_instance, 'type') == 'claim':
            role = 'view_claim'

        shaped = export_loop(model_class, model_instance,
                             field_converter,
                             role=role, print_none=print_none)

        if shaped and len(shaped) == 0 and self.allow_none():
            return shaped
        elif shaped:
            return shaped
        elif print_none:
            return shaped


class CPVClassification(Classification):
    scheme = StringType(required=True, default=u'CPV', choices=[u'CPV', u'ДК021'])
    _id_field_validators = Classification._id_field_validators + (cpv_validator,)

    def validate_scheme(self, data, scheme):
        schematics_document = get_schematics_document(data['__parent__'])
        if (
            get_document_creation_date(schematics_document) > CPV_BLOCK_FROM
            and scheme != u'ДК021'
        ):
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode([u'ДК021'])))


class AdditionalClassification(Classification):

    _id_field_validators = Classification._id_field_validators + (atc_inn_validator,)


class Unit(BaseUnit):
    """
    Extends BaseUnit adding value field to it.
    """

    value = ModelType(Value)


class Document(Model):
    documentType_choices = (
        'awardNotice',
        'bidders',
        'biddingDocuments',
        'billOfQuantity',
        'clarifications',
        'commercialProposal',
        'complaints',
        'conflictOfInterest',
        'contractAnnexe',
        'contractArrangements',
        'contractGuarantees',
        'contractNotice',
        'contractProforma',
        'contractSchedule',
        'contractSigned',
        'debarments',
        'eligibilityCriteria',
        'eligibilityDocuments',
        'evaluationCriteria',
        'evaluationReports',
        'notice',
        'qualificationDocuments',
        'registerExtract',
        'riskProvisions',
        'shortlistedFirms',
        'subContract',
        'technicalSpecifications',
        'tenderNotice',
        'winningBid',
    )

    class Options:
        roles = {
            'create': blacklist('id', 'datePublished', 'dateModified', 'author', 'download_url'),
            'edit': blacklist('id', 'url', 'datePublished', 'dateModified', 'author', 'hash', 'download_url'),
            'embedded': (blacklist('url', 'download_url') + schematics_embedded_role),
            'default': blacklist("__parent__"),
            'view': (blacklist('revisions') + schematics_default_role),
            'revisions': whitelist('url', 'dateModified'),
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    hash = HashType()
    documentType = StringType(choices=documentType_choices)
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


class Identifier(BaseIdentifier):
    # The scheme that holds the unique identifiers used to identify the item being identified.
    scheme = StringType(required=True, choices=ORA_CODES)


class IdentifierAuctions(Identifier):
    """It uses shorter list of ORA Codes"""
    scheme = StringType(required=True, choices=ORA_CODES_AUCTIONS)


class Item(Model):
    """A good, service, or work to be contracted."""
    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    classification = ModelType(CPVClassification)
    additionalClassifications = ListType(ModelType(AdditionalClassification), default=list())
    unit = ModelType(Unit)  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required
    deliveryDate = ModelType(Period)
    deliveryAddress = ModelType(Address)
    deliveryLocation = ModelType(Location)
    relatedLot = MD5Type()


class Organization(BaseOrganization):
    identifier = ModelType(Identifier, required=True)
    additionalIdentifiers = ListType(ModelType(Identifier))


class dgfOrganization(Organization):
    identifier = ModelType(IdentifierAuctions, required=True)
    additionalIdentifiers = ListType(ModelType(IdentifierAuctions))


class ProcuringEntity(dgfOrganization):
    """An organization."""
    class Options:
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
            'edit_active.enquiries': schematics_default_role + blacklist("kind"),
            'edit_active.tendering': schematics_default_role + blacklist("kind"),
        }

    kind = StringType(choices=['general', 'special', 'defense', 'other'])


class SwiftsureProcuringEntity(ProcuringEntity):
    additionalContactPoints = ListType(ModelType(ContactPoint), default=list())


class Revision(Model):
    author = StringType()
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())
    rev = StringType()


class Contract(Model):
    id = MD5Type(required=True, default=lambda: uuid4().hex)
    awardID = StringType()
    contractID = StringType()
    contractNumber = StringType()
    title = StringType()  # Contract title
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # Contract description
    description_en = StringType()
    description_ru = StringType()
    status = StringType(choices=['pending', 'terminated', 'active', 'cancelled'], default='pending')
    period = ModelType(Period)
    value = ModelType(Value)
    dateSigned = IsoDateTimeType()
    documents = ListType(ModelType(Document), default=list())
    items = ListType(ModelType(Item))
    suppliers = ListType(ModelType(Organization), min_size=1, max_size=1)
    date = IsoDateTimeType()


class Cancellation(Model):
    class Options:
        roles = {
            'create': whitelist('reason', 'status', 'cancellationOf', 'relatedLot'),
            'edit': whitelist('status'),
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    reason = StringType(required=True)
    reason_en = StringType()
    reason_ru = StringType()
    date = IsoDateTimeType(default=get_now)
    status = StringType(choices=['pending', 'active'], default='pending')
    documents = ListType(ModelType(Document), default=list())
    cancellationOf = StringType(required=True, choices=['tender', 'lot'], default='tender')
    relatedLot = MD5Type()

    def validate_relatedLot(self, data, relatedLot):
        if not relatedLot and data.get('cancellationOf') == 'lot':
            raise ValidationError(u'This field is required.')
        if (
            relatedLot
            and isinstance(data['__parent__'], Model)
            and relatedLot
            not in [i.id for i in data['__parent__'].lots]
        ):
            raise ValidationError(u"relatedLot should be one of lots")


def validate_features_uniq(features):
    validate_uniq(features,
                  'code', u"Feature code should be uniq for all features")


def validate_lots_uniq(lots):
    validate_uniq(lots, 'id', u"Lot id should be uniq for all lots")

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
    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
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


class AssetCustodian(ocds_organization):
    name = StringType(required=True)
    kind = StringType(choices=['general', 'special', 'other'])
    additionalContactPoints = ListType(ModelType(ContactPoint), default=list())


class AssetHolder(ocds_organization):
    name = StringType(required=True)
    address = ModelType(Address)
    contactPoint = ModelType(ContactPoint)
    additionalContactPoints = ListType(ModelType(ContactPoint), default=list())
    kind = StringType(choices=['general', 'special', 'other'])
