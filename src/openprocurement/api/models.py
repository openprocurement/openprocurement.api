# -*- coding: utf-8 -*-
import datetime
from uuid import uuid4
from couchdb_schematics.document import SchematicsDocument
from schematics.models import Model
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, FloatType, IntType, URLType, DateTimeType, BooleanType, BaseType, EmailType
from schematics.types.compound import ModelType, ListType, DictType
from schematics.types.serializable import serializable


class AmendmentInformation(Model):
    """Amendment information"""
    amendmentDate = DateTimeType()
    amendedFields = StringType()  # Comma-seperated list of affected fields.
    justification = StringType()  # An explanation / justification for the amendment.


class Notice(Model):
    """The notice is a published document that notifies the public at various stages of the contracting process."""
    id = StringType()  # The identifier that identifies the notice to the publisher. This may be the same or different from the OCID.
    uri = URLType()  # A permanent uri that provides access to the notice.
    publishedDate = DateTimeType()  # The date this version of the notice was published. In the case of notice amendments, it is the date that reflects to this version of the data.
    isAmendment = BooleanType()  # If true, then amendment information should be provided.
    amendment = ModelType(AmendmentInformation)  # Amendment information


class Value(Model):
    amount = FloatType()  # Amount as a number.
    currency = StringType(max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.
    valueAddedTaxIncluded = BooleanType(default=True)


class Period(Model):
    """The period when the tender is open for submissions. The end date is the closing date for tender submissions."""
    startDate = DateTimeType()  # The state date for the period.
    endDate = DateTimeType()  # The end date for the period.


class classification(Model):
    scheme = StringType(required=True)  # The classification scheme for the goods
    id = StringType(required=True)  # The classification ID from the Scheme used
    description = StringType(required=True)  # A description of the goods, services to be provided.
    uri = URLType()


class Item(Model):
    """A good, service, or work to be contracted."""
    description = StringType()  # A description of the goods, services to be provided.
    primaryClassification = ModelType(classification)
    additionalClassification = ListType(ModelType(classification), default=list())
    unitOfMeasure = StringType()  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required
    valuePerUnit = ModelType(Value)  # The value per unit of the item specified.


class Document(Model):
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": SchematicsDocument.Options.roles['embedded'],
            "view": (blacklist("revisions") + SchematicsDocument.Options.roles['default']),
            "revisions": whitelist("uri", "modified"),
        }

    id = StringType(required=True)
    classification = StringType(choices=['notice', 'biddingDocuments', 'technicalSpecifications', 'evaluationCriteria', 'clarifications', 'bidders'])
    title = StringType()  # A title of the document.
    description = StringType()  # A description of the document.
    format = StringType()
    url = URLType()  # Link to the document or attachment.
    datePublished = DateTimeType(default=datetime.datetime.now)
    modified = DateTimeType(default=datetime.datetime.now)  # Date that the document was last modified
    language = StringType()


class identifier(Model):
    class Options:
        serialize_when_none = False

    name = StringType(required=True)
    scheme = URLType()  # The scheme that holds the unique identifiers used to identify the item being identified.
    uid = StringType()  # The unique ID for this entity under the given ID scheme.
    uri = URLType()


class address(Model):
    class Options:
        serialize_when_none = False

    streetAddress = StringType()
    locality = StringType()
    region = StringType()
    postalCode = StringType()
    countryName = StringType()


class ContactPoint(Model):
    name = StringType(required=True)
    email = EmailType(required=True)
    telephone = StringType()
    faxNumber = StringType()
    url = URLType()


class Organization(Model):
    """An organization."""
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": SchematicsDocument.Options.roles['embedded'],
            "view": SchematicsDocument.Options.roles['default'],
        }

    id = ModelType(identifier, required=True)
    address = ModelType(address)
    contactPoint = ModelType(ContactPoint)


class Bid(Model):
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": SchematicsDocument.Options.roles['embedded'],
            "view": SchematicsDocument.Options.roles['default'],
            "auction": whitelist("totalValue"),
        }

    bidders = ListType(ModelType(Organization), default=list())
    date = DateTimeType(default=datetime.datetime.now)
    id = StringType(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['registration', 'validBid', 'invalidBid'])
    totalValue = ModelType(Value)
    documents = ListType(ModelType(Document), default=list())


class Award(Model):
    """ An award for the given procurement. There may be more than one award
        per contracting process e.g. because the contract is split amongst
        different providers, or because it is a standing offer.
    """
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": SchematicsDocument.Options.roles['embedded'],
            "view": SchematicsDocument.Options.roles['default'],
        }

    awardID = StringType(required=True, default=lambda: uuid4().hex)
    notice = ModelType(Notice)
    awardDate = DateTimeType(default=datetime.datetime.now)
    awardValue = ModelType(Value)
    awardStatus = StringType(required=True, choices=['pending', 'unsuccessful'])  # 'pending', 'active', 'cancelled', 'unsuccessful'
    suppliers = ListType(ModelType(Organization), default=list())
    itemsAwarded = ListType(ModelType(Item))


class revision(Model):
    date = DateTimeType(default=datetime.datetime.now)
    changes = ListType(DictType(BaseType), default=list())


class Tender(Model):
    """Data regarding tender process - publicly inviting prospective contractors to submit bids for evaluation and selecting a winner or winners."""
    tenderID = StringType(required=True, default=lambda: "UA-{}".format(uuid4().hex))  # TenderID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    notice = ModelType(Notice)
    itemsToBeProcured = ListType(ModelType(Item))  # The goods and services to be purchased, broken into line items wherever possible. Items should not be duplicated, but a quantity of 2 specified instead.
    totalValue = ModelType(Value)  # The total estimated value of the procurement.
    method = StringType(choices=['Open', 'Selective', 'Limited'])  # Specify tendering method as per GPA definitions of Open, Selective, Limited (http://www.wto.org/english/docs_e/legal_e/rev-gpr-94_01_e.htm)
    methodJustification = StringType()  # Justification of procurement method, especially in the case of Limited tendering.
    selectionCriteria = StringType(choices=['Lowest Cost', 'Best Proposal', 'Best Value to Government', 'Single bid only'])  # Specify the selection criteria, by lowest cost,
    selectionDetails = StringType()  # Any detailed or further information on the selection criteria.
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
    minimalStep = ModelType(Value)
    status = StringType(choices=['enquiries', 'tendering', 'auction', 'qualification', 'awarded', 'contract-signed', 'paused'], default='enquiries')


class OrganizationDocument(SchematicsDocument, Organization):
    pass


class TenderDocument(SchematicsDocument, Tender):
    class Options:
        roles = {
            "plain": (blacklist("_attachments", "revisions", "modified") + SchematicsDocument.Options.roles['embedded']),
            "view": (blacklist("_attachments", "revisions") + SchematicsDocument.Options.roles['embedded']),
            "listing": whitelist("modified", "doc_id"),
            "auction": whitelist("modified", "bids", "tenderPeriod", "minimalStep"),
        }

    _attachments = DictType(DictType(BaseType), default=dict())
    modified = DateTimeType(default=datetime.datetime.now)

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
