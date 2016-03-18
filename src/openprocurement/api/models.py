# -*- coding: utf-8 -*-
import os
from couchdb_schematics.document import SchematicsDocument
from datetime import datetime, timedelta
from iso8601 import parse_date, ParseError
from pytz import timezone
from pyramid.security import Allow
from schematics.exceptions import ConversionError, ValidationError
from schematics.models import Model as SchematicsModel
from schematics.transforms import whitelist, blacklist, export_loop, convert
from schematics.types import StringType, FloatType, IntType, URLType, BooleanType, BaseType, EmailType, MD5Type
from schematics.types.compound import ModelType, DictType, ListType as BaseListType
from schematics.types.serializable import serializable
from uuid import uuid4
from barbecue import vnmax
from zope.interface import implementer, Interface


STAND_STILL_TIME = timedelta(days=1)
COMPLAINT_STAND_STILL_TIME = timedelta(days=3)
BIDDER_TIME = timedelta(minutes=6)
SERVICE_TIME = timedelta(minutes=9)
AUCTION_STAND_STILL_TIME = timedelta(minutes=15)

schematics_embedded_role = SchematicsDocument.Options.roles['embedded'] + blacklist("__parent__")
schematics_default_role = SchematicsDocument.Options.roles['default'] + blacklist("__parent__")

TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')


def get_now():
    return datetime.now(TZ)


def read_json(name):
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)


CPV_CODES = read_json('cpv.json')
#DKPP_CODES = read_json('dkpp.json')
ORA_CODES = [i['code'] for i in read_json('OrganisationRegistrationAgency.json')['data']]


class ITender(Interface):
    """ Base tender marker interface """


class IsoDateTimeType(BaseType):
    MESSAGES = {
        'parse': u'Could not parse {0}. Should be ISO8601.',
    }

    def to_native(self, value, context=None):
        if isinstance(value, datetime):
            return value
        try:
            date = parse_date(value, None)
            if not date.tzinfo:
                date = TZ.localize(date)
            return date
        except ParseError:
            raise ConversionError(self.messages['parse'].format(value))
        except OverflowError as e:
            raise ConversionError(e.message)

    def to_primitive(self, value, context=None):
        return value.isoformat()


def set_parent(item, parent):
    if hasattr(item, '__parent__') and item.__parent__ is None:
        item.__parent__ = parent


def get_tender(model):
    while not ITender.providedBy(model):
        model = model.__parent__
    return model


class ListType(BaseListType):

    def export_loop(self, list_instance, field_converter,
                    role=None, print_none=False):
        """Loops over each item in the model and applies either the field
        transform or the multitype transform.  Essentially functions the same
        as `transforms.export_loop`.
        """
        data = []
        for value in list_instance:
            if hasattr(self.field, 'export_loop'):
                shaped = self.field.export_loop(value, field_converter,
                                                role=role,
                                                print_none=print_none)
                feels_empty = shaped and len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            # Print if we want empty or found a value
            if feels_empty and self.field.allow_none():
                data.append(shaped)
            elif shaped is not None:
                data.append(shaped)
            elif print_none:
                data.append(shaped)

        # Return data if the list contains anything
        if len(data) > 0:
            return data
        elif len(data) == 0 and self.allow_none():
            return data
        elif print_none:
            return data


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


class Model(SchematicsModel):
    class Options(object):
        """Export options for Document."""
        serialize_when_none = False
        roles = {
            "default": blacklist("__parent__"),
            "embedded": blacklist("__parent__"),
        }

    __parent__ = BaseType()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for k in self._fields:
                if k != '__parent__' and self.get(k) != other.get(k):
                    return False
            return True
        return NotImplemented

    def convert(self, raw_data, **kw):
        """
        Converts the raw data into richer Python constructs according to the
        fields on the model
        """
        value = convert(self.__class__, raw_data, **kw)
        for i, j in value.items():
            if isinstance(j, list):
                for x in j:
                    set_parent(x, self)
            else:
                set_parent(j, self)
        return value

    def to_patch(self, role=None):
        """
        Return data as it would be validated. No filtering of output unless
        role is defined.
        """
        field_converter = lambda field, value: field.to_primitive(value)
        data = export_loop(self.__class__, self, field_converter, role=role, raise_error_on_role=True, print_none=True)
        return data

    def get_role(self):
        root = self.__parent__
        while root.__parent__ is not None:
            root = root.__parent__
        request = root.request
        return 'Administrator' if request.authenticated_role == 'Administrator' else 'edit'


class Value(Model):

    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    currency = StringType(required=True, default=u'UAH', max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.
    valueAddedTaxIncluded = BooleanType(required=True, default=True)


class Guarantee(Model):
    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    currency = StringType(required=True, default=u'UAH', max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.


class Period(Model):
    """The period when the tender is open for submissions. The end date is the closing date for tender submissions."""

    startDate = IsoDateTimeType()  # The state date for the period.
    endDate = IsoDateTimeType()  # The end date for the period.

    def validate_startDate(self, data, value):
        if value and data.get('endDate') and data.get('endDate') < value:
            raise ValidationError(u"period should begin before its end")


def calc_auction_end_time(bids, start):
    return start + bids * BIDDER_TIME + SERVICE_TIME + AUCTION_STAND_STILL_TIME


class TenderAuctionPeriod(Period):
    """The auction period."""

    @serializable(serialize_when_none=False)
    def shouldStartAfter(self):
        if self.endDate:
            return
        tender = self.__parent__
        if tender.lots or tender.status not in ['active.tendering', 'active.auction']:
            return
        if self.startDate and get_now() > calc_auction_end_time(tender.numberOfBids, self.startDate):
            return calc_auction_end_time(tender.numberOfBids, self.startDate).isoformat()
        else:
            return tender.tenderPeriod.endDate.isoformat()


class LotAuctionPeriod(Period):
    """The auction period."""

    @serializable(serialize_when_none=False)
    def shouldStartAfter(self):
        if self.endDate:
            return
        tender = get_tender(self)
        lot = self.__parent__
        if tender.status not in ['active.tendering', 'active.auction'] or lot.status != 'active':
            return
        if tender.status == 'active.auction' and lot.numberOfBids < 2:
            return
        if self.startDate and get_now() > calc_auction_end_time(lot.numberOfBids, self.startDate):
            return calc_auction_end_time(lot.numberOfBids, self.startDate).isoformat()
        else:
            return tender.tenderPeriod.endDate.isoformat()


class PeriodEndRequired(Period):
    endDate = IsoDateTimeType(required=True)  # The end date for the period.


class Classification(Model):

    scheme = StringType(required=True)  # The classification scheme for the goods
    id = StringType(required=True)  # The classification ID from the Scheme used
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    uri = URLType()


class CPVClassification(Classification):
    scheme = StringType(required=True, default=u'CPV', choices=[u'CPV'])
    id = StringType(required=True, choices=CPV_CODES)


class Unit(Model):
    """Description of the unit which the good comes in e.g. hours, kilograms. Made up of a unit name, and the value of a single unit."""

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


ADDITIONAL_CLASSIFICATIONS_SCHEMES = [u'ДКПП', u'NONE', u'ДК003', u'ДК015', u'ДК018']


def validate_dkpp(items, *args):
    if items and not any([i.scheme in ADDITIONAL_CLASSIFICATIONS_SCHEMES for i in items]):
        raise ValidationError(u"One of additional classifications should be one of [{0}].".format(', '.join(ADDITIONAL_CLASSIFICATIONS_SCHEMES)))


class Item(Model):
    """A good, service, or work to be contracted."""

    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    classification = ModelType(CPVClassification, required=True)
    additionalClassifications = ListType(ModelType(Classification), default=list(), required=True, min_size=1, validators=[validate_dkpp])
    unit = ModelType(Unit)  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required
    deliveryDate = ModelType(Period)
    deliveryAddress = ModelType(Address)
    deliveryLocation = ModelType(Location)
    relatedLot = MD5Type()

    def validate_relatedLot(self, data, relatedLot):
        if relatedLot and isinstance(data['__parent__'], Model) and relatedLot not in [i.id for i in get_tender(data['__parent__']).lots]:
            raise ValidationError(u"relatedLot should be one of lots")


class Document(Model):
    class Options:
        roles = {
            'edit': blacklist('id', 'url', 'datePublished', 'dateModified', ''),
            'embedded': schematics_embedded_role,
            'view': (blacklist('revisions') + schematics_default_role),
            'revisions': whitelist('url', 'dateModified'),
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    documentType = StringType(choices=[
        'tenderNotice', 'awardNotice', 'contractNotice',
        'notice', 'biddingDocuments', 'technicalSpecifications',
        'evaluationCriteria', 'clarifications', 'shortlistedFirms',
        'riskProvisions', 'billOfQuantity', 'bidders', 'conflictOfInterest',
        'debarments', 'evaluationReports', 'winningBid', 'complaints',
        'contractSigned', 'contractArrangements', 'contractSchedule',
        'contractAnnexe', 'contractGuarantees', 'subContract',
        'eligibilityCriteria',
    ])
    title = StringType()  # A title of the document.
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # A description of the document.
    description_en = StringType()
    description_ru = StringType()
    format = StringType(regex='^[-\w]+/[-\.\w\+]+$')
    url = StringType()  # Link to the document or attachment.
    datePublished = IsoDateTimeType(default=get_now)
    dateModified = IsoDateTimeType(default=get_now)  # Date that the document was last dateModified
    language = StringType()
    documentOf = StringType(required=True, choices=['tender', 'item', 'lot'], default='tender')
    relatedItem = MD5Type()
    author = StringType()

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

    def validate_relatedItem(self, data, relatedItem):
        if not relatedItem and data.get('documentOf') in ['item', 'lot']:
            raise ValidationError(u'This field is required.')
        if relatedItem and isinstance(data['__parent__'], Model):
            tender = get_tender(data['__parent__'])
            if data.get('documentOf') == 'lot' and relatedItem not in [i.id for i in tender.lots]:
                raise ValidationError(u"relatedItem should be one of lots")
            if data.get('documentOf') == 'item' and relatedItem not in [i.id for i in tender.items]:
                raise ValidationError(u"relatedItem should be one of items")


class Identifier(Model):

    scheme = StringType(required=True, choices=ORA_CODES)  # The scheme that holds the unique identifiers used to identify the item being identified.
    id = BaseType(required=True)  # The identifier of the organization in the selected scheme.
    legalName = StringType()  # The legally registered name of the organization.
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # A URI to identify the organization.


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


class Parameter(Model):

    code = StringType(required=True)
    value = FloatType(required=True)

    def validate_code(self, data, code):
        if isinstance(data['__parent__'], Model) and code not in [i.code for i in (get_tender(data['__parent__']).features or [])]:
            raise ValidationError(u"code should be one of feature code.")

    def validate_value(self, data, value):
        if isinstance(data['__parent__'], Model):
            tender = get_tender(data['__parent__'])
            codes = dict([(i.code, [x.value for x in i.enum]) for i in (tender.features or [])])
            if data['code'] in codes and value not in codes[data['code']]:
                raise ValidationError(u"value should be one of feature value.")


def validate_parameters_uniq(parameters, *args):
    if parameters:
        codes = [i.code for i in parameters]
        if [i for i in set(codes) if codes.count(i) > 1]:
            raise ValidationError(u"Parameter code should be uniq for all parameters")


class LotValue(Model):
    class Options:
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
            'create': whitelist('value', 'relatedLot'),
            'edit': whitelist('value', 'relatedLot'),
            'auction_view': whitelist('value', 'date', 'relatedLot', 'participationUrl'),
            'auction_post': whitelist('value', 'date', 'relatedLot'),
            'auction_patch': whitelist('participationUrl', 'relatedLot'),
        }

    value = ModelType(Value, required=True)
    relatedLot = MD5Type(required=True)
    participationUrl = URLType()
    date = IsoDateTimeType(default=get_now)

    def validate_value(self, data, value):
        if value and isinstance(data['__parent__'], Model) and data['relatedLot']:
            lots = [i for i in get_tender(data['__parent__']).lots if i.id == data['relatedLot']]
            if not lots:
                return
            lot = lots[0]
            if lot.value.amount < value.amount:
                raise ValidationError(u"value of bid should be less than value of lot")
            if lot.get('value').currency != value.currency:
                raise ValidationError(u"currency of bid should be identical to currency of value of lot")
            if lot.get('value').valueAddedTaxIncluded != value.valueAddedTaxIncluded:
                raise ValidationError(u"valueAddedTaxIncluded of bid should be identical to valueAddedTaxIncluded of value of lot")

    def validate_relatedLot(self, data, relatedLot):
        if isinstance(data['__parent__'], Model) and relatedLot not in [i.id for i in get_tender(data['__parent__']).lots]:
            raise ValidationError(u"relatedLot should be one of lots")


view_bid_role = (blacklist('owner_token', 'owner') + schematics_default_role)
Administrator_bid_role = whitelist('tenderers')


class Bid(Model):
    class Options:
        roles = {
            'Administrator': Administrator_bid_role,
            'embedded': view_bid_role,
            'view': view_bid_role,
            'create': whitelist('value', 'guarantee', 'tenderers', 'parameters', 'lotValues'),
            'edit': whitelist('value', 'guarantee', 'tenderers', 'parameters', 'lotValues'),
            'auction_view': whitelist('value', 'lotValues', 'id', 'date', 'parameters', 'participationUrl'),
            'auction_post': whitelist('value', 'lotValues', 'id', 'date'),
            'auction_patch': whitelist('id', 'lotValues', 'participationUrl'),
            'active.enquiries': whitelist(),
            'active.tendering': whitelist(),
            'active.auction': whitelist(),
            'active.qualification': view_bid_role,
            'active.awarded': view_bid_role,
            'complete': view_bid_role,
            'unsuccessful': view_bid_role,
            'cancelled': view_bid_role,
        }

    def __local_roles__(self):
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'bid_owner')])

    tenderers = ListType(ModelType(Organization), required=True, min_size=1, max_size=1)
    parameters = ListType(ModelType(Parameter), default=list(), validators=[validate_parameters_uniq])
    lotValues = ListType(ModelType(LotValue), default=list())
    date = IsoDateTimeType(default=get_now)
    id = MD5Type(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['registration', 'validBid', 'invalidBid'])
    value = ModelType(Value)
    documents = ListType(ModelType(Document), default=list())
    participationUrl = URLType()
    owner_token = StringType()
    owner = StringType()
    guarantee = ModelType(Guarantee)

    __name__ = ''

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_bid'),
        ]

    def validate_participationUrl(self, data, url):
        if url and isinstance(data['__parent__'], Model) and get_tender(data['__parent__']).lots:
            raise ValidationError(u"url should be posted for each lot of bid")

    def validate_lotValues(self, data, values):
        if isinstance(data['__parent__'], Model):
            tender = data['__parent__']
            if tender.lots and not values:
                raise ValidationError(u'This field is required.')

    def validate_value(self, data, value):
        if isinstance(data['__parent__'], Model):
            tender = data['__parent__']
            if tender.lots:
                if value:
                    raise ValidationError(u"value should be posted for each lot of bid")
            else:
                if not value:
                    raise ValidationError(u'This field is required.')
                if tender.value.amount < value.amount:
                    raise ValidationError(u"value of bid should be less than value of tender")
                if tender.get('value').currency != value.currency:
                    raise ValidationError(u"currency of bid should be identical to currency of value of tender")
                if tender.get('value').valueAddedTaxIncluded != value.valueAddedTaxIncluded:
                    raise ValidationError(u"valueAddedTaxIncluded of bid should be identical to valueAddedTaxIncluded of value of tender")

    def validate_parameters(self, data, parameters):
        if isinstance(data['__parent__'], Model):
            tender = data['__parent__']
            if tender.lots:
                lots = [i.relatedLot for i in data['lotValues']]
                items = [i.id for i in tender.items if i.relatedLot in lots]
                codes = dict([
                    (i.code, [x.value for x in i.enum])
                    for i in (tender.features or [])
                    if i.featureOf == 'tenderer' or i.featureOf == 'lot' and i.relatedItem in lots or i.featureOf == 'item' and i.relatedItem in items
                ])
                if set([i['code'] for i in parameters]) != set(codes):
                    raise ValidationError(u"All features parameters is required.")
            elif not parameters and tender.features:
                raise ValidationError(u'This field is required.')
            elif set([i['code'] for i in parameters]) != set([i.code for i in (tender.features or [])]):
                raise ValidationError(u"All features parameters is required.")


class Revision(Model):
    author = StringType()
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())
    rev = StringType()


class Question(Model):
    class Options:
        roles = {
            'create': whitelist('author', 'title', 'description', 'questionOf', 'relatedItem'),
            'edit': whitelist('answer'),
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
            'active.enquiries': (blacklist('author') + schematics_embedded_role),
            'active.tendering': (blacklist('author') + schematics_embedded_role),
            'active.auction': (blacklist('author') + schematics_embedded_role),
            'active.qualification': schematics_default_role,
            'active.awarded': schematics_default_role,
            'complete': schematics_default_role,
            'unsuccessful': schematics_default_role,
            'cancelled': schematics_default_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    author = ModelType(Organization, required=True)  # who is asking question (contactPoint - person, identification - organization that person represents)
    title = StringType(required=True)  # title of the question
    description = StringType()  # description of the question
    date = IsoDateTimeType(default=get_now)  # autogenerated date of posting
    answer = StringType()  # only tender owner can post answer
    questionOf = StringType(required=True, choices=['tender', 'item', 'lot'], default='tender')
    relatedItem = StringType(min_length=1)

    def validate_relatedItem(self, data, relatedItem):
        if not relatedItem and data.get('questionOf') in ['item', 'lot']:
            raise ValidationError(u'This field is required.')
        if relatedItem and isinstance(data['__parent__'], Model):
            tender = get_tender(data['__parent__'])
            if data.get('questionOf') == 'lot' and relatedItem not in [i.id for i in tender.lots]:
                raise ValidationError(u"relatedItem should be one of lots")
            if data.get('questionOf') == 'item' and relatedItem not in [i.id for i in tender.items]:
                raise ValidationError(u"relatedItem should be one of items")


class Complaint(Model):
    class Options:
        roles = {
            'create': whitelist('author', 'title', 'description', 'status', 'relatedLot'),
            'draft': whitelist('author', 'title', 'description', 'status'),
            'cancellation': whitelist('cancellationReason', 'status'),
            'satisfy': whitelist('satisfied', 'status'),
            'answer': whitelist('resolution', 'resolutionType', 'status', 'tendererAction'),
            'action': whitelist('tendererAction'),
            'review': whitelist('decision', 'status'),
            'view': view_bid_role,
            'view_claim': (blacklist('author') + view_bid_role),
            'active.enquiries': view_bid_role,
            'active.tendering': view_bid_role,
            'active.auction': view_bid_role,
            'active.qualification': view_bid_role,
            'active.awarded': view_bid_role,
            'complete': view_bid_role,
            'unsuccessful': view_bid_role,
            'cancelled': view_bid_role,
        }
    # system
    id = MD5Type(required=True, default=lambda: uuid4().hex)
    complaintID = StringType()
    date = IsoDateTimeType(default=get_now)  # autogenerated date of posting
    status = StringType(choices=['draft', 'claim', 'answered', 'pending', 'invalid', 'resolved', 'declined', 'cancelled'], default='draft')
    documents = ListType(ModelType(Document), default=list())
    type = StringType(choices=['claim', 'complaint'], default='claim')  # 'complaint' if status in ['pending'] or 'claim' if status in ['draft', 'claim', 'answered']
    owner_token = StringType()
    owner = StringType()
    relatedLot = MD5Type()
    # complainant
    author = ModelType(Organization, required=True)  # author of claim
    title = StringType(required=True)  # title of the claim
    description = StringType()  # description of the claim
    dateSubmitted = IsoDateTimeType()
    # tender owner
    resolution = StringType()
    resolutionType = StringType(choices=['invalid', 'resolved', 'declined'])
    dateAnswered = IsoDateTimeType()
    tendererAction = StringType()
    tendererActionDate = IsoDateTimeType()
    # complainant
    satisfied = BooleanType()
    dateEscalated = IsoDateTimeType()
    # reviewer
    decision = StringType()
    dateDecision = IsoDateTimeType()
    # complainant
    cancellationReason = StringType()
    dateCanceled = IsoDateTimeType()

    def serialize(self, role=None, context=None):
        if role == 'view' and self.type == 'claim' and get_tender(self).status in ['active.enquiries', 'active.tendering']:
            role = 'view_claim'
        return super(Complaint, self).serialize(role=role, context=context)

    def get_role(self):
        root = self.__parent__
        while root.__parent__ is not None:
            root = root.__parent__
        request = root.request
        data = request.json_body['data']
        if request.authenticated_role == 'complaint_owner' and data.get('status', self.status) == 'cancelled':
            role = 'cancellation'
        elif request.authenticated_role == 'complaint_owner' and self.status == 'draft':
            role = 'draft'
        elif request.authenticated_role == 'tender_owner' and self.status == 'claim':
            role = 'answer'
        elif request.authenticated_role == 'tender_owner' and self.status == 'pending':
            role = 'action'
        elif request.authenticated_role == 'complaint_owner' and self.status == 'answered':
            role = 'satisfy'
        elif request.authenticated_role == 'reviewers' and self.status == 'pending':
            role = 'review'
        else:
            role = 'invalid'
        return role

    def __local_roles__(self):
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'complaint_owner')])

    def __acl__(self):
        return [
            (Allow, 'g:reviewers', 'edit_complaint'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_complaint'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_complaint_documents'),
        ]

    def validate_resolutionType(self, data, resolutionType):
        if not resolutionType and data.get('status') == 'answered':
            raise ValidationError(u'This field is required.')

    def validate_cancellationReason(self, data, cancellationReason):
        if not cancellationReason and data.get('status') == 'cancelled':
            raise ValidationError(u'This field is required.')

    def validate_relatedLot(self, data, relatedLot):
        if relatedLot and isinstance(data['__parent__'], Model) and relatedLot not in [i.id for i in get_tender(data['__parent__']).lots]:
            raise ValidationError(u"relatedLot should be one of lots")


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
        if relatedLot and isinstance(data['__parent__'], Model) and relatedLot not in [i.id for i in data['__parent__'].lots]:
            raise ValidationError(u"relatedLot should be one of lots")


class Contract(Model):
    class Options:
        roles = {
            'create': blacklist('id', 'status', 'documents', 'dateSigned'),
            'edit': blacklist('id', 'documents', 'awardID', 'suppliers', 'items', 'contractID'),
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    awardID = StringType(required=True)
    contractID = StringType()
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

    def validate_awardID(self, data, awardID):
        if awardID and isinstance(data['__parent__'], Model) and awardID not in [i.id for i in data['__parent__'].awards]:
            raise ValidationError(u"awardID should be one of awards")

    def validate_dateSigned(self, data, value):
        if value and isinstance(data['__parent__'], Model):
            award = [i for i in data['__parent__'].awards if i.id == data['awardID']][0]
            if award.complaintPeriod.endDate >= value:
                raise ValidationError(u"Contract signature date should be after award complaint period end date ({})".format(award.complaintPeriod.endDate.isoformat()))
            if value > get_now():
                raise ValidationError(u"Contract signature date can't be in the future")


class Award(Model):
    """ An award for the given procurement. There may be more than one award
        per contracting process e.g. because the contract is split amongst
        different providers, or because it is a standing offer.
    """
    class Options:
        roles = {
            'create': blacklist('id', 'status', 'date', 'documents', 'complaints', 'complaintPeriod'),
            'edit': whitelist('status'),
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
            'Administrator': whitelist('complaintPeriod'),
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    bid_id = MD5Type(required=True)
    lotID = MD5Type()
    title = StringType()  # Award title
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # Award description
    description_en = StringType()
    description_ru = StringType()
    status = StringType(required=True, choices=['pending', 'unsuccessful', 'active', 'cancelled'], default='pending')
    date = IsoDateTimeType(default=get_now)
    value = ModelType(Value)
    suppliers = ListType(ModelType(Organization), required=True, min_size=1, max_size=1)
    items = ListType(ModelType(Item))
    documents = ListType(ModelType(Document), default=list())
    complaints = ListType(ModelType(Complaint), default=list())
    complaintPeriod = ModelType(Period)

    def validate_lotID(self, data, lotID):
        if isinstance(data['__parent__'], Model):
            if not lotID and data['__parent__'].lots:
                raise ValidationError(u'This field is required.')
            if lotID and lotID not in [i.id for i in data['__parent__'].lots]:
                raise ValidationError(u"lotID should be one of lots")


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
        if data.get('featureOf') == 'item' and isinstance(data['__parent__'], Model) and relatedItem not in [i.id for i in data['__parent__'].items]:
            raise ValidationError(u"relatedItem should be one of items")
        if data.get('featureOf') == 'lot' and isinstance(data['__parent__'], Model) and relatedItem not in [i.id for i in data['__parent__'].lots]:
            raise ValidationError(u"relatedItem should be one of lots")


default_lot_role = (blacklist('numberOfBids') + schematics_default_role)
embedded_lot_role = (blacklist('numberOfBids') + schematics_embedded_role)


class Lot(Model):
    class Options:
        roles = {
            'create': whitelist('id', 'title', 'title_en', 'title_ru', 'description', 'description_en', 'description_ru', 'value', 'minimalStep'),
            'edit': whitelist('title', 'title_en', 'title_ru', 'description', 'description_en', 'description_ru', 'value', 'minimalStep'),
            'embedded': embedded_lot_role,
            'view': default_lot_role,
            'default': default_lot_role,
            'auction_view': default_lot_role,
            'auction_patch': whitelist('id', 'auctionUrl'),
            'chronograph': whitelist('id', 'auctionPeriod'),
            'chronograph_view': whitelist('id', 'auctionPeriod', 'numberOfBids', 'status'),
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    title = StringType(required=True, min_length=1)
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    value = ModelType(Value, required=True)
    minimalStep = ModelType(Value, required=True)
    auctionPeriod = ModelType(LotAuctionPeriod, default={})
    auctionUrl = URLType()
    status = StringType(choices=['active', 'cancelled', 'unsuccessful', 'complete'], default='active')

    @serializable
    def numberOfBids(self):
        """A property that is serialized by schematics exports."""
        bids = [
            bid
            for bid in self.__parent__.bids
            if self.id in [i.relatedLot for i in bid.lotValues]
        ]
        return len(bids)

    @serializable(serialized_name="value", type=ModelType(Value))
    def lot_value(self):
        return Value(dict(amount=self.value.amount,
                          currency=self.__parent__.value.currency,
                          valueAddedTaxIncluded=self.__parent__.value.valueAddedTaxIncluded))

    @serializable(serialized_name="minimalStep", type=ModelType(Value))
    def lot_minimalStep(self):
        return Value(dict(amount=self.minimalStep.amount,
                          currency=self.__parent__.minimalStep.currency,
                          valueAddedTaxIncluded=self.__parent__.minimalStep.valueAddedTaxIncluded))

    def validate_minimalStep(self, data, value):
        if value and value.amount and data.get('value'):
            if data.get('value').amount < value.amount:
                raise ValidationError(u"value should be less than value of lot")


def validate_features_uniq(features, *args):
    if features:
        codes = [i.code for i in features]
        if any([codes.count(i) > 1 for i in set(codes)]):
            raise ValidationError(u"Feature code should be uniq for all features")


def validate_items_uniq(items, *args):
    if items:
        ids = [i.id for i in items]
        if [i for i in set(ids) if ids.count(i) > 1]:
            raise ValidationError(u"Item id should be uniq for all items")


def validate_lots_uniq(lots, *args):
    if lots:
        ids = [i.id for i in lots]
        if [i for i in set(ids) if ids.count(i) > 1]:
            raise ValidationError(u"Lot id should be uniq for all lots")


def validate_cpv_group(items, *args):
    if items and len(set([i.classification.id[:3] for i in items])) != 1:
        raise ValidationError(u"CPV group of items be identical")


plain_role = (blacklist('_attachments', 'revisions', 'dateModified') + schematics_embedded_role)
create_role = (blacklist('owner_token', 'owner', '_attachments', 'revisions', 'dateModified', 'doc_id', 'tenderID', 'bids', 'documents', 'awards', 'questions', 'complaints', 'auctionUrl', 'status', 'auctionPeriod', 'awardPeriod', 'procurementMethod', 'awardCriteria', 'submissionMethod', 'cancellations') + schematics_embedded_role)
edit_role = (blacklist('status', 'procurementMethodType', 'lots', 'owner_token', 'owner', '_attachments', 'revisions', 'dateModified', 'doc_id', 'tenderID', 'bids', 'documents', 'awards', 'questions', 'complaints', 'auctionUrl', 'auctionPeriod', 'awardPeriod', 'procurementMethod', 'awardCriteria', 'submissionMethod', 'mode', 'cancellations') + schematics_embedded_role)
view_role = (blacklist('owner_token', '_attachments', 'revisions') + schematics_embedded_role)
listing_role = whitelist('dateModified', 'doc_id')
auction_view_role = whitelist('tenderID', 'dateModified', 'bids', 'auctionPeriod', 'minimalStep', 'auctionUrl', 'features', 'lots')
auction_post_role = whitelist('bids')
auction_patch_role = whitelist('auctionUrl', 'bids', 'lots')
enquiries_role = (blacklist('owner_token', '_attachments', 'revisions', 'bids', 'numberOfBids') + schematics_embedded_role)
auction_role = (blacklist('owner_token', '_attachments', 'revisions', 'bids', 'numberOfBids') + schematics_embedded_role)
#chronograph_role = whitelist('status', 'enquiryPeriod', 'tenderPeriod', 'auctionPeriod', 'awardPeriod', 'lots')
chronograph_role = whitelist('auctionPeriod', 'lots', 'next_check')
chronograph_view_role = whitelist('status', 'enquiryPeriod', 'tenderPeriod', 'auctionPeriod', 'awardPeriod', 'awards', 'lots', 'doc_id', 'submissionMethodDetails', 'mode', 'numberOfBids', 'complaints')
Administrator_role = whitelist('status', 'mode', 'procuringEntity')


@implementer(ITender)
class Tender(SchematicsDocument, Model):
    """Data regarding tender process - publicly inviting prospective contractors to submit bids for evaluation and selecting a winner or winners."""
    class Options:
        roles = {
            'plain': plain_role,
            'create': create_role,
            'edit': edit_role,
            'edit_active.enquiries': edit_role,
            'edit_active.tendering': whitelist(),
            'edit_active.auction': whitelist(),
            'edit_active.qualification': whitelist(),
            'edit_active.awarded': whitelist(),
            'edit_complete': whitelist(),
            'edit_unsuccessful': whitelist(),
            'edit_cancelled': whitelist(),
            'view': view_role,
            'listing': listing_role,
            'auction_view': auction_view_role,
            'auction_post': auction_post_role,
            'auction_patch': auction_patch_role,
            'active.enquiries': enquiries_role,
            'active.tendering': enquiries_role,
            'active.auction': auction_role,
            'active.qualification': view_role,
            'active.awarded': view_role,
            'complete': view_role,
            'unsuccessful': view_role,
            'cancelled': view_role,
            'chronograph': chronograph_role,
            'chronograph_view': chronograph_view_role,
            'Administrator': Administrator_role,
            'default': schematics_default_role,
        }

    def __local_roles__(self):
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'tender_owner')])

    title = StringType(required=True)
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    tenderID = StringType()  # TenderID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    items = ListType(ModelType(Item), required=True, min_size=1, validators=[validate_cpv_group, validate_items_uniq])  # The goods and services to be purchased, broken into line items wherever possible. Items should not be duplicated, but a quantity of 2 specified instead.
    value = ModelType(Value, required=True)  # The total estimated value of the procurement.
    procurementMethod = StringType(choices=['open', 'selective', 'limited'], default='open')  # Specify tendering method as per GPA definitions of Open, Selective, Limited (http://www.wto.org/english/docs_e/legal_e/rev-gpr-94_01_e.htm)
    procurementMethodRationale = StringType()  # Justification of procurement method, especially in the case of Limited tendering.
    procurementMethodRationale_en = StringType()
    procurementMethodRationale_ru = StringType()
    awardCriteria = StringType(choices=['lowestCost', 'bestProposal', 'bestValueToGovernment', 'singleBidOnly'], default='lowestCost')  # Specify the selection criteria, by lowest cost,
    awardCriteriaDetails = StringType()  # Any detailed or further information on the selection criteria.
    awardCriteriaDetails_en = StringType()
    awardCriteriaDetails_ru = StringType()
    submissionMethod = StringType(choices=['electronicAuction', 'electronicSubmission', 'written', 'inPerson'], default='electronicAuction')  # Specify the method by which bids must be submitted, in person, written, or electronic auction
    submissionMethodDetails = StringType()  # Any detailed or further information on the submission method.
    submissionMethodDetails_en = StringType()
    submissionMethodDetails_ru = StringType()
    enquiryPeriod = ModelType(PeriodEndRequired, required=True)  # The period during which enquiries may be made and will be answered.
    tenderPeriod = ModelType(PeriodEndRequired, required=True)  # The period when the tender is open for submissions. The end date is the closing date for tender submissions.
    hasEnquiries = BooleanType()  # A Yes/No field as to whether enquiries were part of tender process.
    eligibilityCriteria = StringType()  # A description of any eligibility criteria for potential suppliers.
    eligibilityCriteria_en = StringType()
    eligibilityCriteria_ru = StringType()
    awardPeriod = ModelType(Period)  # The date or period on which an award is anticipated to be made.
    numberOfBidders = IntType()  # The number of unique tenderers who participated in the tender
    #numberOfBids = IntType()  # The number of bids or submissions to the tender. In the case of an auction, the number of bids may differ from the numberOfBidders.
    bids = ListType(ModelType(Bid), default=list())  # A list of all the companies who entered submissions for the tender.
    procuringEntity = ModelType(Organization, required=True)  # The entity managing the procurement, which may be different from the buyer who is paying / using the items being procured.
    documents = ListType(ModelType(Document), default=list())  # All documents and attachments related to the tender.
    awards = ListType(ModelType(Award), default=list())
    contracts = ListType(ModelType(Contract), default=list())
    revisions = ListType(ModelType(Revision), default=list())
    auctionPeriod = ModelType(TenderAuctionPeriod, default={})
    minimalStep = ModelType(Value, required=True)
    status = StringType(choices=['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded', 'complete', 'cancelled', 'unsuccessful'], default='active.enquiries')
    questions = ListType(ModelType(Question), default=list())
    complaints = ListType(ComplaintModelType(Complaint), default=list())
    auctionUrl = URLType()
    mode = StringType(choices=['test'])
    cancellations = ListType(ModelType(Cancellation), default=list())
    features = ListType(ModelType(Feature), validators=[validate_features_uniq])
    lots = ListType(ModelType(Lot), default=list(), validators=[validate_lots_uniq])

    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    dateModified = IsoDateTimeType()
    owner_token = StringType()
    owner = StringType()

    procurementMethodType = StringType(default="belowThreshold")

    __name__ = ''

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        elif request.authenticated_role == 'chronograph':
            role = 'chronograph'
        elif request.authenticated_role == 'auction':
            role = 'auction_{}'.format(request.method.lower())
        else:
            role = 'edit_{}'.format(request.context.status)
        return role

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(i.owner, i.owner_token), 'create_award_complaint')
            for i in self.bids
        ]
        acl.extend([
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_tender'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_tender_documents'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_complaint'),
        ])
        return acl

    def __repr__(self):
        return '<%s:%r@%r>' % (type(self).__name__, self.id, self.rev)

    def initialize(self):
        if not self.enquiryPeriod.startDate:
            self.enquiryPeriod.startDate = get_now()
        if not self.tenderPeriod.startDate:
            self.tenderPeriod.startDate = self.enquiryPeriod.endDate

    @serializable(serialize_when_none=False)
    def next_check(self):
        now = get_now()
        checks = []
        if self.status == 'active.enquiries' and self.tenderPeriod.startDate:
            checks.append(self.tenderPeriod.startDate.astimezone(TZ))
        elif self.status == 'active.enquiries' and self.enquiryPeriod.endDate:
            checks.append(self.enquiryPeriod.endDate.astimezone(TZ))
        elif self.status == 'active.tendering' and self.tenderPeriod.endDate:
            checks.append(self.tenderPeriod.endDate.astimezone(TZ))
        elif not self.lots and self.status == 'active.auction' and self.auctionPeriod and self.auctionPeriod.startDate and not self.auctionPeriod.endDate:
            if now < self.auctionPeriod.startDate:
                checks.append(self.auctionPeriod.startDate.astimezone(TZ))
            elif now < calc_auction_end_time(self.numberOfBids, self.auctionPeriod.startDate).astimezone(TZ):
                checks.append(calc_auction_end_time(self.numberOfBids, self.auctionPeriod.startDate).astimezone(TZ))
        elif self.lots and self.status == 'active.auction':
            for lot in self.lots:
                if lot.status != 'active' or not lot.auctionPeriod or not lot.auctionPeriod.startDate or lot.auctionPeriod.endDate:
                    continue
                if now < lot.auctionPeriod.startDate:
                    checks.append(lot.auctionPeriod.startDate.astimezone(TZ))
                elif now < calc_auction_end_time(lot.numberOfBids, lot.auctionPeriod.startDate).astimezone(TZ):
                    checks.append(calc_auction_end_time(lot.numberOfBids, lot.auctionPeriod.startDate).astimezone(TZ))
        elif not self.lots and self.status == 'active.awarded':
            standStillEnds = [
                a.complaintPeriod.endDate.astimezone(TZ)
                for a in self.awards
                if a.complaintPeriod.endDate
            ]
            if standStillEnds:
                standStillEnd = max(standStillEnds)
                if standStillEnd > now:
                    checks.append(standStillEnd)
        elif self.lots and self.status in ['active.qualification', 'active.awarded']:
            lots_ends = []
            for lot in self.lots:
                if lot['status'] != 'active':
                    continue
                lot_awards = [i for i in self.awards if i.lotID == lot.id]
                standStillEnds = [
                    a.complaintPeriod.endDate.astimezone(TZ)
                    for a in lot_awards
                    if a.complaintPeriod.endDate
                ]
                if not standStillEnds:
                    continue
                standStillEnd = max(standStillEnds)
                if standStillEnd > now:
                    lots_ends.append(standStillEnd)
            if lots_ends:
                checks.append(min(lots_ends))
        if self.status.startswith('active'):
            for complaint in self.complaints:
                if complaint.status == 'claim' and complaint.dateSubmitted:
                    checks.append(complaint.dateSubmitted + COMPLAINT_STAND_STILL_TIME)
                elif complaint.status == 'answered' and complaint.dateAnswered:
                    checks.append(complaint.dateAnswered + COMPLAINT_STAND_STILL_TIME)
            for award in self.awards:
                for complaint in award.complaints:
                    if complaint.status == 'claim' and complaint.dateSubmitted:
                        checks.append(complaint.dateSubmitted + COMPLAINT_STAND_STILL_TIME)
                    elif complaint.status == 'answered' and complaint.dateAnswered:
                        checks.append(complaint.dateAnswered + COMPLAINT_STAND_STILL_TIME)
        return min(checks).isoformat() if checks else None

    @serializable
    def numberOfBids(self):
        """A property that is serialized by schematics exports."""
        return len(self.bids)

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id

    @serializable(serialized_name="value", type=ModelType(Value))
    def tender_value(self):
        return Value(dict(amount=sum([i.value.amount for i in self.lots]),
                          currency=self.value.currency,
                          valueAddedTaxIncluded=self.value.valueAddedTaxIncluded)) if self.lots else self.value

    @serializable(serialized_name="minimalStep", type=ModelType(Value))
    def tender_minimalStep(self):
        return Value(dict(amount=min([i.minimalStep.amount for i in self.lots]),
                          currency=self.minimalStep.currency,
                          valueAddedTaxIncluded=self.minimalStep.valueAddedTaxIncluded)) if self.lots else self.minimalStep

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if data[k] == self.__class__.fields[k].default or data[k] == getattr(self, k)]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self

    def validate_features(self, data, features):
        if features and data['lots'] and any([
            round(vnmax([
                i
                for i in features
                if i.featureOf == 'tenderer' or i.featureOf == 'lot' and i.relatedItem != lot['id'] or i.featureOf == 'item' and i.relatedItem in [j.id for j in data['items'] if j.relatedLot != lot['id']]
            ]), 15) > 0.3
            for lot in data['lots']
        ]):
            raise ValidationError(u"Sum of max value of all features for lot should be less then or equal to 30%")
        elif features and not data['lots'] and round(vnmax(features), 15) > 0.3:
            raise ValidationError(u"Sum of max value of all features should be less then or equal to 30%")

    def validate_auctionUrl(self, data, url):
        if url and data['lots']:
            raise ValidationError(u"url should be posted for each lot")

    def validate_minimalStep(self, data, value):
        if value and value.amount and data.get('value'):
            if data.get('value').amount < value.amount:
                raise ValidationError(u"value should be less than value of tender")
            if data.get('value').currency != value.currency:
                raise ValidationError(u"currency should be identical to currency of value of tender")
            if data.get('value').valueAddedTaxIncluded != value.valueAddedTaxIncluded:
                raise ValidationError(u"valueAddedTaxIncluded should be identical to valueAddedTaxIncluded of value of tender")

    def validate_tenderPeriod(self, data, period):
        if period and period.startDate and data.get('enquiryPeriod') and data.get('enquiryPeriod').endDate and period.startDate < data.get('enquiryPeriod').endDate:
            raise ValidationError(u"period should begin after enquiryPeriod")

    def validate_awardPeriod(self, data, period):
        if period and period.startDate and data.get('auctionPeriod') and data.get('auctionPeriod').endDate and period.startDate < data.get('auctionPeriod').endDate:
            raise ValidationError(u"period should begin after auctionPeriod")
        if period and period.startDate and data.get('tenderPeriod') and data.get('tenderPeriod').endDate and period.startDate < data.get('tenderPeriod').endDate:
            raise ValidationError(u"period should begin after tenderPeriod")
