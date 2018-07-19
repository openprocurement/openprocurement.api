# -*- coding: utf-8 -*-
from couchdb_schematics.document import SchematicsDocument

from schematics.exceptions import ValidationError, DataError
from schematics.types import StringType, BaseType, FloatType, EmailType, URLType, IntType
from schematics.types.compound import DictType, ListType, ModelType
from schematics.types.serializable import serializable

from openprocurement.api.models.roles import organization_roles, auctionParameters_roles
from openprocurement.api.models.schematics_extender import Model, IsoDateTimeType, SHA512Type
from openprocurement.api.utils import get_now


sensitive_fields = ('__parent__', 'owner_token', 'transfer_token')

sensitive_embedded_role = SchematicsDocument.Options.roles['embedded'] + sensitive_fields


class Revision(Model):
    author = StringType()
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())
    rev = StringType()


class BaseResourceItem(SchematicsDocument, Model):
    owner = StringType()  # the broker
    owner_token = StringType()  # token for broker access
    transfer_token = SHA512Type()  # token wich allows you to change the broker
    mode = StringType(choices=['test'])  # need for switching auction to different states
    dateModified = IsoDateTimeType()
    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    revisions = ListType(ModelType(Revision), default=list())  # couchdb rev

    __name__ = ''

    def __repr__(self):
        return '<%s:%r@%r>' % (type(self).__name__, self.id, self.rev)

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id

    def _dict(self, mapping):
        return dict((key, mapping[key]) for key in mapping)

    def import_data(self, raw_data, recursive=False, **kwargs):
        """
        Converts and imports the raw data into an existing model instance.

        :param raw_data:
            The data to be imported.
        """
        data = self._convert(raw_data, trusted_data=self._dict(self), recursive=recursive, **kwargs)
        self._data.converted.update(data)
        if kwargs.get('validate'):
            self.validate(convert=False)
        return self


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


class Guarantee(Model):
    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    # The currency in 3-letter ISO 4217 format.
    currency = StringType(required=True, default=u'UAH', max_length=3, min_length=3)


class Period(Model):
    """The period when the tender is open for submissions. The end date is the closing date for tender submissions."""

    startDate = IsoDateTimeType()  # The state date for the period.
    endDate = IsoDateTimeType()  # The end date for the period.

    def validate_startDate(self, data, value):
        if value and data.get('endDate') and data.get('endDate') < value:
            raise ValidationError(u"period should begin before its end")


class PeriodEndRequired(Period):
    endDate = IsoDateTimeType(required=True)  # The end date for the period.


class ContactPoint(Model):
    name = StringType(required=True)
    name_en = StringType()
    name_ru = StringType()
    telephone = StringType()
    email = EmailType()
    faxNumber = StringType()
    url = URLType()

    def validate_email(self, data, value):
        if not value and not data.get('telephone'):
            raise ValidationError(u"telephone or email should be present")
        return value


class BaseIdentifier(Model):
    # The scheme that holds the unique identifiers used to identify the item being identified.
    scheme = StringType(required=True, choices=[])
    id = BaseType(required=True)  # The identifier of the organization in the selected scheme.
    legalName = StringType()  # The legally registered name of the organization.
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # A URI to identify the organization.


class Organization(Model):
    """An organization."""
    class Options:
        roles = organization_roles

    name = StringType(required=True)
    name_en = StringType()
    name_ru = StringType()
    identifier = ModelType(BaseIdentifier, required=True)
    additionalIdentifiers = ListType(ModelType(BaseIdentifier))
    address = ModelType(Address, required=True)
    contactPoint = ModelType(ContactPoint, required=True)


class BaseUnit(Model):
    """
    Description of the unit which the good comes in e.g. hours, kilograms.
    Made up of a unit name of a single unit.
    """

    name = StringType()
    name_en = StringType()
    name_ru = StringType()
    code = StringType(required=True)


class BasicValue(Model):
    amount = FloatType(required=True, min_value=0)  # Amount as a number.
    currency = StringType(required=True, max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.


class Classification(Model):
    scheme = StringType(required=True)  # The classification scheme for the goods
    id = StringType(required=True)  # The classification ID from the Scheme used
    description = StringType(required=True)  # A description of the goods, services to be provided.
    description_en = StringType()
    description_ru = StringType()
    uri = URLType()


class UAEDRAndMFOClassification(Classification):
    scheme = StringType(choices=['UA-EDR', 'UA-MFO', 'accountNumber'], required=True)


class BankAccount(Model):
    description = StringType()
    bankName = StringType(required=True)
    accountIdentification = ListType(ModelType(UAEDRAndMFOClassification), default=list(), min_size=1)


class AuctionParameters(Model):
    """Configurable auction parameters"""
    class Options:
        roles = auctionParameters_roles

    type = StringType(choices=['english', 'insider'])
    dutchSteps = IntType(min_value=1, max_value=99, default=None)


class RegistrationDetails(Model):
    status = StringType(choices=['unknown', 'registering', 'complete'], default='unknown')
    registrationID = StringType()
    registrationDate = IsoDateTimeType()

    def validate_registrationID(self, data, value):
        if value and data['status'] != 'complete':
            raise ValidationError(u"You can fill registrationID only when status is complete")

    def validate_registrationDate(self, data, value):
        if value and data['status'] != 'complete':
            raise ValidationError(u"You can fill registrationDate only when status is complete")
