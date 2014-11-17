# -*- coding: utf-8 -*-
from datetime import datetime
from iso8601 import parse_date, ParseError
from uuid import uuid4
from couchdb_schematics.document import SchematicsDocument
from schematics.models import Model
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, FloatType, IntType, URLType, BooleanType, BaseType, EmailType
from schematics.types.compound import ModelType, ListType, DictType
from schematics.types.serializable import serializable
from schematics.exceptions import ConversionError
from tzlocal import get_localzone


schematics_embedded_role = SchematicsDocument.Options.roles['embedded']
schematics_default_role = SchematicsDocument.Options.roles['default']


TZ = get_localzone()


def get_now():
    return datetime.now(TZ)


class IsoDateTimeType(BaseType):
    MESSAGES = {
        'parse': u'Could not parse {0}. Should be ISO8601.',
    }

    def to_native(self, value, context=None):
        if isinstance(value, datetime):
            return value
        try:
            return parse_date(value, TZ)
        except ParseError, e:
            raise ConversionError(e)

    def to_primitive(self, value, context=None):
        return value.isoformat(' ')


class AmendmentInformation(Model):
    """Amendment information"""
    amendmentDate = IsoDateTimeType()
    amendedFields = StringType()  # Comma-seperated list of affected fields.
    justification = StringType()  # An explanation / justification for the amendment.


class Notice(Model):
    """The notice is a published document that notifies the public at various stages of the contracting process."""
    id = StringType()  # The identifier that identifies the notice to the publisher. This may be the same or different from the OCID.
    uri = URLType()  # A permanent uri that provides access to the notice.
    publishedDate = IsoDateTimeType()  # The date this version of the notice was published. In the case of notice amendments, it is the date that reflects to this version of the data.
    isAmendment = BooleanType()  # If true, then amendment information should be provided.
    amendment = ModelType(AmendmentInformation)  # Amendment information


class Value(Model):
    amount = FloatType()  # Amount as a number.
    currency = StringType(max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.
    valueAddedTaxIncluded = BooleanType(default=True)


class Period(Model):
    """The period when the tender is open for submissions. The end date is the closing date for tender submissions."""
    startDate = IsoDateTimeType()  # The state date for the period.
    endDate = IsoDateTimeType()  # The end date for the period.


class Classification(Model):
    scheme = StringType(required=True)  # The classification scheme for the goods
    id = StringType(required=True)  # The classification ID from the Scheme used
    description = StringType(required=True)  # A description of the goods, services to be provided.
    uri = URLType()



class Unit(Model):
    """Description of the unit which the good comes in e.g. hours, kilograms. Made up of a unit name, and the value of a single unit."""
    name = StringType()
    value = ModelType(Value)


class Item(Model):
    """A good, service, or work to be contracted."""
    description = StringType()  # A description of the goods, services to be provided.
    classification = ModelType(Classification)
    additionalClassifications = ListType(ModelType(Classification), default=list())
    unit = ModelType(Unit)  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required


class Document(Model):
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": schematics_embedded_role,
            "view": (blacklist("revisions") + schematics_default_role),
            "revisions": whitelist("uri", "dateModified"),
        }

    id = StringType(required=True)
    classification = StringType(choices=['notice', 'biddingDocuments', 'technicalSpecifications', 'evaluationCriteria', 'clarifications', 'bidders'])
    title = StringType()  # A title of the document.
    description = StringType()  # A description of the document.
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
    uri = URLType()  # A URI to identify the organization.


class address(Model):
    class Options:
        serialize_when_none = False

    streetAddress = StringType()
    locality = StringType()
    region = StringType()
    postalCode = StringType()
    countryName = StringType()


class ContactPoint(Model):
    name = StringType()
    email = EmailType()
    telephone = StringType()
    faxNumber = StringType()
    url = URLType()


class Organization(Model):
    """An organization."""
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": schematics_embedded_role,
            "view": schematics_default_role,
        }

    name = StringType(required=True)
    identifier = ModelType(Identifier, required=True)
    additionalIdentifiers = ListType(ModelType(Identifier))
    address = ModelType(address)
    contactPoint = ModelType(ContactPoint)


class Bid(Model):
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": schematics_embedded_role,
            "view": schematics_default_role,
            "auction_view": whitelist("value"),
            "enquiries": whitelist(),
            "tendering": whitelist(),
            "auction": whitelist("value"),
            "qualification": whitelist("value"),
            "awarded": whitelist("value"),
            "contract-signed": schematics_default_role,
            "paused": whitelist(),
        }

    bidders = ListType(ModelType(Organization), default=list())
    date = IsoDateTimeType(default=get_now)
    id = StringType(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['registration', 'validBid', 'invalidBid'])
    value = ModelType(Value)
    documents = ListType(ModelType(Document), default=list())


class Award(Model):
    """ An award for the given procurement. There may be more than one award
        per contracting process e.g. because the contract is split amongst
        different providers, or because it is a standing offer.
    """
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": schematics_embedded_role,
            "view": schematics_default_role,
        }

    awardID = StringType(required=True, default=lambda: uuid4().hex)
    notice = ModelType(Notice)
    awardDate = IsoDateTimeType(default=get_now)
    awardValue = ModelType(Value)
    awardStatus = StringType(required=True, choices=['pending', 'unsuccessful'])  # 'pending', 'active', 'cancelled', 'unsuccessful'
    suppliers = ListType(ModelType(Organization), default=list())
    itemsAwarded = ListType(ModelType(Item))


class revision(Model):
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())


class Tender(Model):
    """Data regarding tender process - publicly inviting prospective contractors to submit bids for evaluation and selecting a winner or winners."""
    title = StringType()
    description = StringType()
    tenderID = StringType(required=True, default=lambda: "UA-{}".format(uuid4().hex))  # TenderID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    items = ListType(ModelType(Item))  # The goods and services to be purchased, broken into line items wherever possible. Items should not be duplicated, but a quantity of 2 specified instead.
    value = ModelType(Value)  # The total estimated value of the procurement.
    procurementMethod = StringType(choices=['Open', 'Selective', 'Limited'])  # Specify tendering method as per GPA definitions of Open, Selective, Limited (http://www.wto.org/english/docs_e/legal_e/rev-gpr-94_01_e.htm)
    procurementMethodRationale = StringType()  # Justification of procurement method, especially in the case of Limited tendering.
    awardCriteria = StringType(choices=['Lowest Cost', 'Best Proposal', 'Best Value to Government', 'Single bid only'])  # Specify the selection criteria, by lowest cost,
    awardCriteriaDetails = StringType()  # Any detailed or further information on the selection criteria.
    submissionMethod = StringType(choices=['Electronic Auction', 'Electronic Submission', 'Written', 'In Person'])  # Specify the method by which bids must be submitted, in person, written, or electronic auction
    submissionDetails = StringType()  # Any detailed or further information on the submission method.
    tenderPeriod = ModelType(Period)  # The period when the tender is open for submissions. The end date is the closing date for tender submissions.
    enquiryPeriod = ModelType(Period)  # The period during which enquiries may be made and will be answered.
    hasEnquiries = BooleanType()  # A Yes/No field as to whether enquiries were part of tender process.
    awardPeriod = ModelType(Period)  # The date or period on which an award is anticipated to be made.
    numberOfBidders = IntType()  # The number of unique bidders who participated in the tender
    numberOfBids = IntType()  # The number of bids or submissions to the tender. In the case of an auction, the number of bids may differ from the numberOfBidders.
    bids = ListType(ModelType(Bid), default=list())  # A list of all the companies who entered submissions for the tender.
    procuringEntity = ModelType(Organization)  # The entity managing the procurement, which may be different from the buyer who is paying / using the items being procured.
    documents = ListType(ModelType(Document), default=list())  # All documents and attachments related to the tender.
    awards = ListType(ModelType(Award), default=list())
    revisions = ListType(ModelType(revision), default=list())
    deliveryDate = ModelType(Period)
    auctionPeriod = ModelType(Period)
    minimalStep = ModelType(Value)
    status = StringType(choices=['enquiries', 'tendering', 'auction', 'qualification', 'awarded', 'contract-signed', 'paused'], default='enquiries')


class OrganizationDocument(SchematicsDocument, Organization):
    pass


plain_role = (blacklist("_attachments", "revisions", "dateModified") + schematics_embedded_role)
view_role = (blacklist("_attachments", "revisions") + schematics_embedded_role)
listing_role = whitelist("dateModified", "doc_id")
auction_view_role = whitelist("dateModified", "bids", "tenderPeriod", "minimalStep")
enquiries_role = (blacklist("_attachments", "revisions", "bids") + schematics_embedded_role)


class TenderDocument(SchematicsDocument, Tender):
    class Options:
        roles = {
            "plain": plain_role,
            "view": view_role,
            "listing": listing_role,
            "auction_view": auction_view_role,
            "enquiries": enquiries_role,
            "tendering": enquiries_role,
            "auction": view_role,
            "qualification": view_role,
            "awarded": view_role,
            "contract-signed": view_role,
            "paused": view_role,
        }

    _attachments = DictType(DictType(BaseType), default=dict())
    dateModified = IsoDateTimeType(default=get_now)

    @serializable(serialized_name="id")
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
