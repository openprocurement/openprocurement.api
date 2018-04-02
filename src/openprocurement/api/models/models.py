# -*- coding: utf-8 -*-
from openprocurement.api.models.schematics_extender import Model
from schematics.types import (
    StringType,
    FloatType
)
from openprocurement.api.models.schematics_extender import IsoDateTimeType
from schematics.exceptions import ValidationError


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
