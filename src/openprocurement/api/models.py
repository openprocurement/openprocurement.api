# -*- coding: utf-8 -*-
import datetime
import random
from uuid import uuid4
from couchdb_schematics.document import SchematicsDocument
from schematics.models import Model
from schematics.transforms import blacklist
from schematics.types import StringType, FloatType, IntType, URLType, DateTimeType, BooleanType
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


class Period(Model):
    """The period when the tender is open for submissions. The end date is the closing date for tender submissions."""
    startDate = DateTimeType()  # The state date for the period.
    endDate = DateTimeType()  # The end date for the period.


class Item(Model):
    """A good, service, or work to be contracted."""
    description = StringType()  # A description of the goods, services to be provided.
    classificationScheme = StringType(choices=['CPV', 'GSIN', 'UNSPSC', 'Other'])  # The classification scheme for the goods
    otherClassificationScheme = StringType()  # If the classification schema was not in list, please specify
    classificationID = StringType()  # The classification ID from the Scheme used
    classificationDescription = StringType()  # A description of the goods, services to be provided.
    unitOfMeasure = StringType()  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required
    valuePerUnit = ModelType(Value)  # The value per unit of the item specified.


class Attachment(Model):
    description = StringType()  # A description of the document.
    uri = URLType()  # Link to the document or attachment.
    lastModified = DateTimeType()  # Date that the document was last modified


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


class Organization(Model):
    """An organization."""
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": (blacklist("_id") + SchematicsDocument.Options.roles['embedded']),
            "view": SchematicsDocument.Options.roles['default'],
        }

    id = ModelType(identifier, required=True)
    address = ModelType(address)


class Bid(Model):
    class Options:
        serialize_when_none = False
        roles = {
            "embedded": (blacklist("_id") + SchematicsDocument.Options.roles['embedded']),
            "view": SchematicsDocument.Options.roles['default'],
        }

    bidders = ListType(ModelType(Organization), default=list())
    date = DateTimeType(default=datetime.datetime.now)
    id = StringType(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['registration', 'validBid', 'invalidBid'])
    totalValue = ModelType(Value)


class Tender(Model):
    """Data regarding tender process - publicly inviting prospective contractors to submit bids for evaluation and selecting a winner or winners."""
    tenderID = StringType(required=True, default=lambda: "UA-2014-DUS-{:03}".format(random.randint(0, 10 ** 3)))  # TenderID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
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
    clarificationPeriod = ModelType(Period)  # The period during which clarification requests may be made and will be answered.
    clarifications = BooleanType()  # A Yes/No field as to whether clarifications were issued. Would expect clarifications to appear as amendments.
    awardPeriod = ModelType(Period)  # The date or period on which an award is anticipated to be made.
    numberOfBidders = IntType()  # The number of unique bidders who participated in the tender
    numberOfBids = IntType()  # The number of bids or submissions to the tender. In the case of an auction, the number of bids may differ from the numberOfBidders.
    bids = ListType(ModelType(Bid), default=list())  # A list of all the companies who entered submissions for the tender.
    procuringEntity = ModelType(Organization)  # The entity managing the procurement, which may be different from the buyer who is paying / using the items being procured.
    attachments = ListType(ModelType(Attachment))  # All documents and attachments related to the tender.


class OrganizationDocument(SchematicsDocument, Organization):
    pass


class TenderDocument(SchematicsDocument, Tender):
    class Options:
        roles = {
            "view": (blacklist("_attachments") + SchematicsDocument.Options.roles['embedded']),
        }

    _attachments = DictType(DictType(StringType), default=dict())
    modified = DateTimeType(default=datetime.datetime.now)

    @serializable(serialized_name="id")
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id
