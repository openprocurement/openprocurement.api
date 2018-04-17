# -*- coding: utf-8 -*-
from openprocurement.api.models.schematics_extender import Model
from schematics.types import (
    StringType,
    FloatType
)
from openprocurement.api.constants import IDENTIFIER_CODES
from openprocurement.api.models.schematics_extender import IsoDateTimeType
from schematics.exceptions import ValidationError
from schematics.types import (
    BaseType,
    EmailType,
    URLType
)


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
    email = EmailType()
    telephone = StringType()
    faxNumber = StringType()
    url = URLType()

    def validate_email(self, data, value):
        if not value and not data.get('telephone'):
            raise ValidationError(u"telephone or email should be present")


class Classification(Model):
    # The classification scheme for the goods
    scheme = StringType(required=True)
    # The classification ID from the Scheme used
    id = StringType(required=True)
    # A description of the goods, services to be provided.
    description = StringType(required=True)
    description_en = StringType()
    description_ru = StringType()
    uri = URLType()


class Identifier(Model):
    # The scheme that holds the unique identifiers
    # used to identify the item being identified.
    scheme = StringType(required=True, choices=IDENTIFIER_CODES)
    # The identifier of the organization in the selected scheme.
    id = BaseType(required=True)
    # The legally registered name of the organization.
    legalName = StringType()
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()  # An URI to identify the organization.


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
