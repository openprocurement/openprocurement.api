# -*- coding: utf-8 -*-
import os
from couchdb_schematics.document import SchematicsDocument
from datetime import datetime, timedelta
from iso8601 import parse_date, ParseError
from pytz import timezone
from pyramid.security import Allow
from schematics.exceptions import ConversionError, ValidationError
from schematics.models import Model as SchematicsModel
from schematics.transforms import whitelist, blacklist, export_loop
from schematics.types import StringType, FloatType, IntType, URLType, BooleanType, BaseType, EmailType, MD5Type
from schematics.types.compound import ModelType, ListType, DictType
from schematics.types.serializable import serializable
from tzlocal import get_localzone
from uuid import uuid4


STAND_STILL_TIME = timedelta(days=10)
schematics_embedded_role = SchematicsDocument.Options.roles['embedded']
schematics_default_role = SchematicsDocument.Options.roles['default']

if os.environ.get('READTHEDOCS', None) == 'True':
    os.environ['TZ'] = 'Europe/Kiev'

TZ = timezone(get_localzone().tzname(datetime.now()))


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
DKPP_CODES = read_json('dkpp.json')
ORA_CODES = [i['code'] for i in read_json('OrganisationRegistrationAgency.json')['data']]


class IsoDateTimeType(BaseType):
    MESSAGES = {
        'parse': u'Could not parse {0}. Should be ISO8601.',
    }

    def to_native(self, value, context=None):
        if isinstance(value, datetime):
            return value
        try:
            return parse_date(value, TZ)
        except ParseError:
            raise ConversionError(self.messages['parse'].format(value))

    def to_primitive(self, value, context=None):
        return value.isoformat()


class Model(SchematicsModel):
    def to_patch(self, role=None):
        """Return data as it would be validated. No filtering of output unless
        role is defined.
        """
        field_converter = lambda field, value: field.to_primitive(value)
        data = export_loop(self.__class__, self, field_converter, role=role, raise_error_on_role=True, print_none=True)
        return data


class Value(Model):
    class Options:
        serialize_when_none = False

    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    currency = StringType(required=True, default=u'UAH', max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.
    valueAddedTaxIncluded = BooleanType(required=True, default=True)


class Period(Model):
    """The period when the tender is open for submissions. The end date is the closing date for tender submissions."""
    class Options:
        serialize_when_none = False

    startDate = IsoDateTimeType()  # The state date for the period.
    endDate = IsoDateTimeType()  # The end date for the period.

    def validate_startDate(self, data, value):
        if value and data.get('endDate') and data.get('endDate') < value:
            raise ValidationError(u"period should begin before its end")


class PeriodEndRequired(Period):
    endDate = IsoDateTimeType(required=True)  # The end date for the period.


class Classification(Model):
    class Options:
        serialize_when_none = False

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
    class Options:
        serialize_when_none = False

    name = StringType()
    name_en = StringType()
    name_ru = StringType()
    value = ModelType(Value)
    code = StringType(required=True)


class Address(Model):
    class Options:
        serialize_when_none = False

    streetAddress = StringType()
    locality = StringType()
    region = StringType()
    postalCode = StringType()
    countryName = StringType(required=True)
    countryName_en = StringType()
    countryName_ru = StringType()


class Location(Model):
    class Options:
        serialize_when_none = False

    latitude = BaseType(required=True)
    longitudee = BaseType(required=True)
    elevation = BaseType()


def validate_dkpp(items, *args):
    if items and not any([i.scheme == u'ДКПП' for i in items]):
        raise ValidationError(u"One of additional classifications should be 'ДКПП'")


class Item(Model):
    """A good, service, or work to be contracted."""
    class Options:
        serialize_when_none = False

    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    classification = ModelType(CPVClassification)
    additionalClassifications = ListType(ModelType(Classification), default=list(), validators=[validate_dkpp])
    unit = ModelType(Unit)  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required
    deliveryDate = ModelType(Period)
    deliveryAddress = ModelType(Address)
    deliveryLocation = ModelType(Location)


class Document(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'edit': blacklist('id', 'format', 'url', 'datePublished'),
            'embedded': schematics_embedded_role,
            'view': (blacklist('revisions') + schematics_default_role),
            'revisions': whitelist('url', 'dateModified'),
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    documentType = StringType(choices=[
        'notice', 'biddingDocuments', 'technicalSpecifications',
        'evaluationCriteria', 'clarifications', 'shortlistedFirms',
        'riskProvisions', 'billOfQuantity', 'bidders', 'conflictOfInterest',
        'debarments', 'evaluationReports', 'winningBid', 'complaints',
        'contractSigned', 'contractArrangements', 'contractSchedule',
        'contractAnnexes', 'contractGuarantees', 'subContract'
    ])
    title = StringType()  # A title of the document.
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # A description of the document.
    description_en = StringType()
    description_ru = StringType()
    format = StringType()
    url = StringType()  # Link to the document or attachment.
    datePublished = IsoDateTimeType(default=get_now)
    dateModified = IsoDateTimeType(default=get_now)  # Date that the document was last dateModified
    language = StringType()


class Identifier(Model):
    class Options:
        serialize_when_none = False

    scheme = StringType(required=True, choices=ORA_CODES)  # The scheme that holds the unique identifiers used to identify the item being identified.
    id = BaseType(required=True)  # The identifier of the organization in the selected scheme.
    legalName = StringType()  # The legally registered name of the organization.
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # A URI to identify the organization.


class ContactPoint(Model):
    class Options:
        serialize_when_none = False

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
        serialize_when_none = False
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


view_bid_role = (blacklist('owner_token', 'owner') + schematics_default_role)


class Bid(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'embedded': view_bid_role,
            'view': view_bid_role,
            'create': whitelist('value', 'tenderers'),
            'edit': whitelist('value', 'tenderers'),
            'auction_view': whitelist('value', 'id', 'date', 'participationUrl'),
            'auction_post': whitelist('value', 'id'),
            'auction_patch': whitelist('id', 'participationUrl'),
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
    date = IsoDateTimeType(default=get_now)
    id = MD5Type(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['registration', 'validBid', 'invalidBid'])
    value = ModelType(Value, required=True)
    documents = ListType(ModelType(Document), default=list())
    participationUrl = URLType()
    owner_token = StringType()
    owner = StringType()

    __parent__ = None
    __name__ = ''

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_bid'),
        ]


class Revision(Model):
    author = StringType()
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())


class Question(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'create': whitelist('author', 'title', 'description'),
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


class Complaint(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'create': whitelist('author', 'title', 'description'),
            'edit': whitelist('status', 'resolution'),
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    author = ModelType(Organization, required=True)  # who is asking question (contactPoint - person, identification - organization that person represents)
    title = StringType(required=True)  # title of the question
    description = StringType()  # description of the question
    date = IsoDateTimeType(default=get_now)  # autogenerated date of posting
    status = StringType(choices=['pending', 'invalid', 'resolved', 'declined', 'cancelled'], default='pending')
    resolution = StringType()  # only tender
    documents = ListType(ModelType(Document), default=list())


class Contract(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'create': blacklist('id', 'status', 'documents', 'dateSigned'),
            'edit': blacklist('id', 'documents'),
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    awardID = StringType(required=True)
    title = StringType()  # Contract title
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # Contract description
    description_en = StringType()
    description_ru = StringType()
    status = StringType(required=True, choices=['pending', 'terminated', 'active', 'cancelled'], default='pending')
    period = ModelType(Period)
    value = ModelType(Value)
    dateSigned = IsoDateTimeType()
    documents = ListType(ModelType(Document), default=list())


class Award(Model):
    """ An award for the given procurement. There may be more than one award
        per contracting process e.g. because the contract is split amongst
        different providers, or because it is a standing offer.
    """
    class Options:
        serialize_when_none = False
        roles = {
            'create': blacklist('id', 'status', 'date', 'documents', 'complaints', 'contracts'),
            'edit': whitelist('status'),
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    bid_id = StringType(required=True)
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
    contracts = ListType(ModelType(Contract), default=list())


plain_role = (blacklist('_attachments', 'revisions', 'dateModified') + schematics_embedded_role)
create_role = (blacklist('owner_token', 'owner', '_attachments', 'revisions', 'dateModified', 'doc_id', 'tenderID', 'bids', 'documents', 'awards', 'questions', 'complaints', 'auctionUrl', 'status', 'auctionPeriod', 'awardPeriod', 'procurementMethod', 'awardCriteria', 'submissionMethod') + schematics_embedded_role)
edit_role = (blacklist('owner_token', 'owner', '_attachments', 'revisions', 'dateModified', 'doc_id', 'tenderID', 'bids', 'documents', 'awards', 'questions', 'complaints', 'auctionUrl', 'auctionPeriod', 'awardPeriod', 'procurementMethod', 'awardCriteria', 'submissionMethod') + schematics_embedded_role)
cancel_role = whitelist('status')
view_role = (blacklist('owner', 'owner_token', '_attachments', 'revisions') + schematics_embedded_role)
listing_role = whitelist('dateModified', 'doc_id')
auction_view_role = whitelist('tenderID', 'dateModified', 'bids', 'auctionPeriod', 'minimalStep', 'auctionUrl')
auction_post_role = whitelist('bids')
auction_patch_role = whitelist('auctionUrl', 'bids')
enquiries_role = (blacklist('owner', 'owner_token', '_attachments', 'revisions', 'bids', 'numberOfBids') + schematics_embedded_role)
auction_role = (blacklist('owner', 'owner_token', '_attachments', 'revisions', 'bids') + schematics_embedded_role)
chronograph_role = whitelist('status', 'enquiryPeriod', 'tenderPeriod', 'auctionPeriod', 'awardPeriod')


class Tender(SchematicsDocument, Model):
    """Data regarding tender process - publicly inviting prospective contractors to submit bids for evaluation and selecting a winner or winners."""
    class Options:
        roles = {
            'plain': plain_role,
            'create': create_role,
            'edit': edit_role,
            'edit_active.enquiries': edit_role,
            'edit_active.tendering': cancel_role,
            'edit_active.auction': cancel_role,
            'edit_active.qualification': cancel_role,
            'edit_active.awarded': cancel_role,
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
        }

    def __local_roles__(self):
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'tender_owner')])

    title = StringType()
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    tenderID = StringType()  # TenderID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    items = ListType(ModelType(Item), required=True, min_size=1)  # The goods and services to be purchased, broken into line items wherever possible. Items should not be duplicated, but a quantity of 2 specified instead.
    value = ModelType(Value, required=True)  # The total estimated value of the procurement.
    procurementMethod = StringType(choices=['Open', 'Selective', 'Limited'], default='Open')  # Specify tendering method as per GPA definitions of Open, Selective, Limited (http://www.wto.org/english/docs_e/legal_e/rev-gpr-94_01_e.htm)
    procurementMethodRationale = StringType()  # Justification of procurement method, especially in the case of Limited tendering.
    procurementMethodRationale_en = StringType()
    procurementMethodRationale_ru = StringType()
    awardCriteria = StringType(choices=['Lowest Cost', 'Best Proposal', 'Best Value to Government', 'Single bid only'], default='Lowest Cost')  # Specify the selection criteria, by lowest cost,
    awardCriteriaDetails = StringType()  # Any detailed or further information on the selection criteria.
    awardCriteriaDetails_en = StringType()
    awardCriteriaDetails_ru = StringType()
    submissionMethod = StringType(choices=['Electronic Auction', 'Electronic Submission', 'Written', 'In Person'], default='Electronic Auction')  # Specify the method by which bids must be submitted, in person, written, or electronic auction
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
    revisions = ListType(ModelType(Revision), default=list())
    auctionPeriod = ModelType(Period)
    minimalStep = ModelType(Value, required=True)
    status = StringType(choices=['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded', 'complete', 'cancelled', 'unsuccessful'], default='active.enquiries')
    questions = ListType(ModelType(Question), default=list())
    complaints = ListType(ModelType(Complaint), default=list())
    auctionUrl = URLType()

    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    dateModified = IsoDateTimeType()
    owner_token = StringType()
    owner = StringType()

    __parent__ = None
    __name__ = ''

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(i.owner, i.owner_token), 'create_award_complaint')
            for i in self.bids
        ]
        acl.extend([
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_tender'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'review_complaint'),
        ])
        return acl

    def __repr__(self):
        return '<%s:%r@%r>' % (type(self).__name__, self.id, self.rev)

    @serializable
    def numberOfBids(self):
        """A property that is serialized by schematics exports."""
        return len(self.bids)

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if not data[k]]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self

    def validate_minimalStep(self, data, value):
        if value and value.amount and data.get('value'):
            if data.get('value').amount < value.amount:
                raise ValidationError(u"value should be less than value of tender")
            if data.get('value').currency != value.currency:
                raise ValidationError(u"currency should be identical to currency of value of tender")
            if data.get('value').valueAddedTaxIncluded != value.valueAddedTaxIncluded:
                raise ValidationError(u"valueAddedTaxIncluded should be identical to valueAddedTaxIncluded of value of tender")

    def validate_bids(self, data, bids):
        if bids and data.get('value'):
            if data.get('value').amount < max([i.value.amount for i in bids]):
                raise ValidationError(u"value of bid should be less than value of tender")
            if not all([i.value.currency == data.get('value').currency for i in bids]):
                raise ValidationError(u"currency of bid should be identical to currency of value of tender")
            if not all([i.value.valueAddedTaxIncluded == data.get('value').valueAddedTaxIncluded for i in bids]):
                raise ValidationError(u"valueAddedTaxIncluded of bid should be identical to valueAddedTaxIncluded of value of tender")

    def validate_tenderPeriod(self, data, period):
        if period and period.startDate and data.get('enquiryPeriod') and data.get('enquiryPeriod').endDate and period.startDate < data.get('enquiryPeriod').endDate:
            raise ValidationError(u"period should begin after enquiryPeriod")

    def validate_auctionPeriod(self, data, period):
        if period and period.startDate and data.get('tenderPeriod') and data.get('tenderPeriod').endDate and period.startDate < data.get('tenderPeriod').endDate:
            raise ValidationError(u"period should begin after tenderPeriod")

    def validate_awardPeriod(self, data, period):
        if period and period.startDate and data.get('auctionPeriod') and data.get('auctionPeriod').endDate and period.startDate < data.get('auctionPeriod').endDate:
            raise ValidationError(u"period should begin after auctionPeriod")
        if period and period.startDate and data.get('tenderPeriod') and data.get('tenderPeriod').endDate and period.startDate < data.get('tenderPeriod').endDate:
            raise ValidationError(u"period should begin after tenderPeriod")
