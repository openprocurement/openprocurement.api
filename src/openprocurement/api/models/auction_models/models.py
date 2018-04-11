# -*- coding: utf-8 -*-
from uuid import uuid4

from couchdb_schematics.document import SchematicsDocument
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist, export_loop
from schematics.types import (
    StringType,
    FloatType,
    URLType,
    IntType,
    BooleanType,
    BaseType,
    EmailType,
    MD5Type
)
from schematics.types.compound import (
    ModelType,
    DictType
)
from schematics.types.serializable import serializable

from openprocurement.api.constants import (
    CPV_CODES, ORA_CODES, DK_CODES, CPV_BLOCK_FROM, ATC_CODES, INN_CODES, ATC_INN_CLASSIFICATIONS_FROM,
)
from openprocurement.api.models.schematics_extender import (
    Model,
    ListType,
    IsoDateTimeType,
    HashType
)
from openprocurement.api.models.models import Period
from openprocurement.api.utils import get_now, get_schematics_document, serialize_document_url
from openprocurement.api.validation import validate_uniq

schematics_default_role = SchematicsDocument.Options.roles['default'] + blacklist("__parent__")
schematics_embedded_role = SchematicsDocument.Options.roles['embedded'] + blacklist("__parent__")

plain_role = (blacklist('_attachments', 'revisions', 'dateModified') + schematics_embedded_role)
listing_role = whitelist('dateModified', 'doc_id')
draft_role = whitelist('status')


class Value(Model):
    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, default=u'UAH', max_length=3, min_length=3)
    valueAddedTaxIncluded = BooleanType(required=True, default=True)


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


class Classification(Model):
    scheme = StringType(required=True)  # The classification scheme for the goods
    id = StringType(required=True)  # The classification ID from the Scheme used
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    uri = URLType()


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
    id = StringType(required=True)

    def validate_id(self, data, code):
        if data.get('scheme') == u'CPV' and code not in CPV_CODES:
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(CPV_CODES)))
        elif data.get('scheme') == u'ДК021' and code not in DK_CODES:
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(DK_CODES)))

    def validate_scheme(self, data, scheme):
        schematics_document = get_schematics_document(data['__parent__'])
        if (
            (
                schematics_document.get('revisions')[0].date
                if schematics_document.get('revisions')
                else get_now()
            )
            > CPV_BLOCK_FROM
            and scheme != u'ДК021'
        ):
            raise ValidationError(BaseType.MESSAGES['choices'].format(unicode([u'ДК021'])))


class AdditionalClassification(Classification):

    def validate_id(self, data, code):
        schematics_document = get_schematics_document(data['__parent__'])
        if (
            (
                schematics_document.get('revisions')[0].date
                if schematics_document.get('revisions')
                else get_now()
            )
            > ATC_INN_CLASSIFICATIONS_FROM
        ):
            if data.get('scheme') == u'ATC' and code not in ATC_CODES:
                raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(ATC_CODES)))
            elif data.get('scheme') == u'INN' and code not in INN_CODES:
                raise ValidationError(BaseType.MESSAGES['choices'].format(unicode(INN_CODES)))


class Unit(Model):
    """Description of the unit which the good comes in e.g. hours, kilograms.
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
    documentType = StringType(choices=[
        'tenderNotice', 'awardNotice', 'contractNotice',
        'notice', 'biddingDocuments', 'technicalSpecifications',
        'evaluationCriteria', 'clarifications', 'shortlistedFirms',
        'riskProvisions', 'billOfQuantity', 'bidders', 'conflictOfInterest',
        'debarments', 'evaluationReports', 'winningBid', 'complaints',
        'contractSigned', 'contractArrangements', 'contractSchedule',
        'contractAnnexe', 'contractGuarantees', 'subContract',
        'eligibilityCriteria', 'contractProforma', 'commercialProposal',
        'qualificationDocuments', 'eligibilityDocuments', 'registerExtract',
    ])
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
    # The scheme that holds the unique identifiers used to identify the item being identified.
    scheme = StringType(required=True, choices=ORA_CODES)
    id = BaseType(required=True)  # The identifier of the organization in the selected scheme.
    legalName = StringType()  # The legally registered name of the organization.
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # A URI to identify the organization.


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
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    name = StringType(required=True)
    name_en = StringType()
    name_ru = StringType()
    identifier = ModelType(Identifier, required=True)
    additionalIdentifiers = ListType(ModelType(Identifier))
    address = ModelType(Address, required=True)
    contactPoint = ModelType(ContactPoint, required=True)


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


def validate_items_uniq(items):
    validate_uniq(items, u"Item id should be uniq for all items")


def validate_features_uniq(features):
    validate_uniq(features, u"Feature code should be uniq for all features")


def validate_lots_uniq(lots):
    validate_uniq(lots, u"Lot id should be uniq for all lots")
