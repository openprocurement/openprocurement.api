# -*- coding: utf-8 -*-
from couchdb_schematics.document import SchematicsDocument
from datetime import datetime, timedelta
from iso8601 import parse_date, ParseError
from pyramid.security import Allow
from schematics.exceptions import ConversionError
from schematics.models import Model
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, FloatType, IntType, URLType, BooleanType, BaseType, EmailType
from schematics.types.compound import ModelType, ListType, DictType
from schematics.types.serializable import serializable
from tzlocal import get_localzone
from uuid import uuid4


STAND_STILL_TIME = timedelta(days=10)
schematics_embedded_role = SchematicsDocument.Options.roles['embedded']
schematics_default_role = SchematicsDocument.Options.roles['default']


TZ = get_localzone()


def get_now():
    return datetime.now(TZ)


def read_cpv():
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, 'cpv.json')
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)


CPV_CODES = read_cpv()


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


class AmendmentInformation(Model):
    """Amendment information"""
    class Options:
        serialize_when_none = False

    amendmentDate = IsoDateTimeType()
    amendedFields = StringType()  # Comma-seperated list of affected fields.
    justification = StringType()  # An explanation / justification for the amendment.


class Notice(Model):
    """The notice is a published document that notifies the public at various stages of the contracting process."""
    class Options:
        serialize_when_none = False

    id = StringType()  # The identifier that identifies the notice to the publisher. This may be the same or different from the OCID.
    uri = URLType()  # A permanent uri that provides access to the notice.
    publishedDate = IsoDateTimeType()  # The date this version of the notice was published. In the case of notice amendments, it is the date that reflects to this version of the data.
    isAmendment = BooleanType()  # If true, then amendment information should be provided.
    amendment = ModelType(AmendmentInformation)  # Amendment information


class Value(Model):
    class Options:
        serialize_when_none = False

    amount = FloatType()  # Amount as a number.
    currency = StringType(default=u'UAH', max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.
    valueAddedTaxIncluded = BooleanType(default=True)


class Period(Model):
    """The period when the tender is open for submissions. The end date is the closing date for tender submissions."""
    class Options:
        serialize_when_none = False

    startDate = IsoDateTimeType()  # The state date for the period.
    endDate = IsoDateTimeType()  # The end date for the period.


class Classification(Model):
    class Options:
        serialize_when_none = False

    scheme = StringType(required=True)  # The classification scheme for the goods
    id = StringType(required=True)  # The classification ID from the Scheme used
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    uri = URLType()


class Unit(Model):
    """Description of the unit which the good comes in e.g. hours, kilograms. Made up of a unit name, and the value of a single unit."""
    class Options:
        serialize_when_none = False

    name = StringType()
    name_en = StringType()
    name_ru = StringType()
    value = ModelType(Value)
    code = StringType(choices=CPV_CODES)


class Item(Model):
    """A good, service, or work to be contracted."""
    class Options:
        serialize_when_none = False

    description = StringType()  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    classification = ModelType(Classification)
    additionalClassifications = ListType(ModelType(Classification), default=list())
    unit = ModelType(Unit)  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required


class Document(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'embedded': schematics_embedded_role,
            'view': (blacklist('revisions') + schematics_default_role),
            'revisions': whitelist('uri', 'dateModified'),
        }

    id = StringType()
    classification = StringType(choices=['notice', 'biddingDocuments', 'technicalSpecifications', 'evaluationCriteria', 'clarifications', 'tenderers'])
    title = StringType()  # A title of the document.
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # A description of the document.
    description_en = StringType()
    description_ru = StringType()
    format = StringType()
    url = URLType()  # Link to the document or attachment.
    datePublished = IsoDateTimeType(default=get_now)
    dateModified = IsoDateTimeType(default=get_now)  # Date that the document was last dateModified
    language = StringType()


class Identifier(Model):
    class Options:
        serialize_when_none = False

    scheme = URLType()  # The scheme that holds the unique identifiers used to identify the item being identified.
    id = BaseType()  # The identifier of the organization in the selected scheme.
    legalName = StringType()  # The legally registered name of the organization.
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # A URI to identify the organization.


class Address(Model):
    class Options:
        serialize_when_none = False

    streetAddress = StringType()
    locality = StringType()
    region = StringType()
    postalCode = StringType()
    countryName = StringType()
    countryName_en = StringType()
    countryName_ru = StringType()


class ContactPoint(Model):
    class Options:
        serialize_when_none = False

    name = StringType()
    name_en = StringType()
    name_ru = StringType()
    email = EmailType()
    telephone = StringType()
    faxNumber = StringType()
    url = URLType()


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
    address = ModelType(Address)
    contactPoint = ModelType(ContactPoint)


class Bid(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
            'auction_view': whitelist('value', 'id', 'date'),
            'active.enquiries': whitelist(),
            'active.tendering': whitelist(),
            'active.auction': whitelist('value'),
            'active.qualification': schematics_default_role,
            'active.awarded': schematics_default_role,
            'complete': schematics_default_role,
            'unsuccessful': schematics_default_role,
            'cancelled': schematics_default_role,
        }

    tenderers = ListType(ModelType(Organization), default=list())
    date = IsoDateTimeType(default=get_now)
    id = StringType(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['registration', 'validBid', 'invalidBid'])
    value = ModelType(Value)
    documents = ListType(ModelType(Document), default=list())


class Revision(Model):
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())


class Question(Model):
    class Options:
        serialize_when_none = False
        roles = {
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

    id = StringType(required=True, default=lambda: uuid4().hex)
    author = ModelType(Organization)  # who is asking question (contactPoint - person, identification - organization that person represents)
    title = StringType(required=True)  # title of the question
    description = StringType(required=True)  # description of the question
    date = IsoDateTimeType(default=get_now)  # autogenerated date of posting
    answer = StringType()  # only tender owner can post answer


class Complaint(Model):
    class Options:
        serialize_when_none = False
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    id = StringType(required=True, default=lambda: uuid4().hex)
    author = ModelType(Organization)  # who is asking question (contactPoint - person, identification - organization that person represents)
    title = StringType(required=True)  # title of the question
    description = StringType(required=True)  # description of the question
    date = IsoDateTimeType(default=get_now)  # autogenerated date of posting
    status = StringType(choices=['accepted', 'invalid', 'satisfied', 'rejected', 'cancelled'], default='accepted')
    resolution = StringType()  # only tender
    documents = ListType(ModelType(Document), default=list())


class Award(Model):
    """ An award for the given procurement. There may be more than one award
        per contracting process e.g. because the contract is split amongst
        different providers, or because it is a standing offer.
    """
    class Options:
        serialize_when_none = False
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    id = StringType(required=True, default=lambda: uuid4().hex)
    bid_id = StringType()
    title = StringType()  # Award title
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # Award description
    description_en = StringType()
    description_ru = StringType()
    status = StringType(required=True, choices=['pending', 'unsuccessful', 'active', 'cancelled'])
    date = IsoDateTimeType(default=get_now)
    value = ModelType(Value)
    suppliers = ListType(ModelType(Organization), default=list())
    items = ListType(ModelType(Item))
    documents = ListType(ModelType(Document), default=list())
    complaints = ListType(ModelType(Complaint), default=list())


plain_role = (blacklist('owner_token', '_attachments', 'revisions', 'dateModified') + schematics_embedded_role)
view_role = (blacklist('owner_token', '_attachments', 'revisions') + schematics_embedded_role)
listing_role = whitelist('dateModified', 'doc_id')
auction_view_role = whitelist('tenderID', 'dateModified', 'bids', 'auctionPeriod', 'minimalStep')
enquiries_role = (blacklist('owner_token', '_attachments', 'revisions', 'bids') + schematics_embedded_role)


class Tender(SchematicsDocument, Model):
    """Data regarding tender process - publicly inviting prospective contractors to submit bids for evaluation and selecting a winner or winners."""
    class Options:
        roles = {
            'plain': plain_role,
            'view': view_role,
            'listing': listing_role,
            'auction_view': auction_view_role,
            'active.enquiries': enquiries_role,
            'active.tendering': enquiries_role,
            'active.auction': view_role,
            'active.qualification': view_role,
            'active.awarded': view_role,
            'complete': view_role,
            'unsuccessful': view_role,
            'cancelled': view_role,
        }

    title = StringType()
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    tenderID = StringType()  # TenderID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    items = ListType(ModelType(Item))  # The goods and services to be purchased, broken into line items wherever possible. Items should not be duplicated, but a quantity of 2 specified instead.
    value = ModelType(Value)  # The total estimated value of the procurement.
    procurementMethod = StringType(choices=['Open', 'Selective', 'Limited'])  # Specify tendering method as per GPA definitions of Open, Selective, Limited (http://www.wto.org/english/docs_e/legal_e/rev-gpr-94_01_e.htm)
    procurementMethodRationale = StringType()  # Justification of procurement method, especially in the case of Limited tendering.
    procurementMethodRationale_en = StringType()
    procurementMethodRationale_ru = StringType()
    awardCriteria = StringType(choices=['Lowest Cost', 'Best Proposal', 'Best Value to Government', 'Single bid only'])  # Specify the selection criteria, by lowest cost,
    awardCriteriaDetails = StringType()  # Any detailed or further information on the selection criteria.
    awardCriteriaDetails_en = StringType()
    awardCriteriaDetails_ru = StringType()
    submissionMethod = StringType(choices=['Electronic Auction', 'Electronic Submission', 'Written', 'In Person'])  # Specify the method by which bids must be submitted, in person, written, or electronic auction
    submissionMethodDetails = StringType()  # Any detailed or further information on the submission method.
    submissionMethodDetails_en = StringType()
    submissionMethodDetails_ru = StringType()
    tenderPeriod = ModelType(Period)  # The period when the tender is open for submissions. The end date is the closing date for tender submissions.
    enquiryPeriod = ModelType(Period)  # The period during which enquiries may be made and will be answered.
    hasEnquiries = BooleanType()  # A Yes/No field as to whether enquiries were part of tender process.
    eligibilityCriteria = StringType()  # A description of any eligibility criteria for potential suppliers.
    eligibilityCriteria_en = StringType()
    eligibilityCriteria_ru = StringType()
    awardPeriod = ModelType(Period)  # The date or period on which an award is anticipated to be made.
    numberOfBidders = IntType()  # The number of unique tenderers who participated in the tender
    numberOfBids = IntType()  # The number of bids or submissions to the tender. In the case of an auction, the number of bids may differ from the numberOfBidders.
    bids = ListType(ModelType(Bid), default=list())  # A list of all the companies who entered submissions for the tender.
    procuringEntity = ModelType(Organization)  # The entity managing the procurement, which may be different from the buyer who is paying / using the items being procured.
    documents = ListType(ModelType(Document), default=list())  # All documents and attachments related to the tender.
    awards = ListType(ModelType(Award), default=list())
    revisions = ListType(ModelType(Revision), default=list())
    deliveryDate = ModelType(Period)
    auctionPeriod = ModelType(Period)
    minimalStep = ModelType(Value)
    status = StringType(choices=['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded', 'complete', 'cancelled', 'unsuccessful'], default='active.enquiries')
    questions = ListType(ModelType(Question), default=list())
    complaints = ListType(ModelType(Complaint), default=list())

    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    dateModified = IsoDateTimeType(default=get_now)
    owner_token = StringType(default=lambda: uuid4().hex)
    owner = StringType()

    __parent__ = None
    __name__ = ''

    def __acl__(self):
        return [
            (Allow, self.owner, 'view_tender'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_tender'),
            (Allow, 'chronograph', 'edit_tender'),
        ]

    def __repr__(self):
        return '<%s:%r@%r>' % (type(self).__name__, self.id, self.rev)

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
