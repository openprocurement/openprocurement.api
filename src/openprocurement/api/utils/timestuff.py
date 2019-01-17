# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime, timedelta, time, date as date_type
from re import compile
from pytz import utc

from openprocurement.api.constants import (
    TZ,
    WORKING_DAYS,
)
from openprocurement.api.utils.common import get_now


ACCELERATOR_RE = compile(r'.accelerator=(?P<accelerator>\d+)')
SECONDS_IN_HOUR = 3600


def round_seconds_to_hours(s):
    """Converts seconds to closest hour

    The cause of creation of this function is to convert some amount
    of seconds to closest amount of hours. This neccesity is caused
    by nondistinct value of UTC offset in different timezones.
    """
    hours = float(s) / SECONDS_IN_HOUR
    reminder = hours % 1
    hours_floor = int(hours)
    if reminder > 0.5:
        return hours_floor + 1
    return hours_floor


def set_timezone(dt, tz=TZ):
    """Set timezone of datetime without actual changing of date and time values

    By default, server's timezone will be set.
    """
    return dt.replace(tzinfo=tz)


def set_specific_hour(date_time, hour):
    """Reset datetime's time to {hour}:00:00, while saving timezone data

    Example:
        2018-1-1T14:12:55+02:00 -> 2018-1-1T02:00:00+02:00, for hour=2
        2018-1-1T14:12:55+02:00 -> 2018-1-1T18:00:00+02:00, for hour=18
    """

    return datetime.combine(date_time.date(), time(hour % 24, tzinfo=date_time.tzinfo))


def set_specific_time(date_time, time_obj):
    """Replace datetime time with some other time object"""

    return datetime.combine(date_time.date(), time_obj)


def specific_time_setting(time_cursor, specific_time=None, specific_hour=None):
    if specific_time:
        return set_specific_time(time_cursor, specific_time)
    elif specific_hour:
        return set_specific_hour(time_cursor, specific_hour)

    return time_cursor


def jump_closest_working_day(date_, backward=False):
    """Search closest working day

    :param date_: date to start counting
    :param backward: search in the past when set to True
    :type: date_: datetime.date
    :type backward: bool
    :rtype: datetime.data
    """
    cursor = copy(date_)

    while True:
        cursor += timedelta(1) if not backward else -timedelta(1)
        if not is_holiday(cursor):
            return cursor


def round_out_day(time_cursor, reverse):
    time_cursor += timedelta(days=1) if not reverse else timedelta()
    time_cursor = set_specific_hour(time_cursor, 0)
    return time_cursor


def is_holiday(date):
    """Check if date is holiday
    Calculation is based on WORKING_DAYS dictionary, constructed in following format:
        <date_string>: <bool>

    where:
        - `date_string` - string representing the date in ISO 8601 format, `YYYY-MM-DD`.
        - `bool` - boolean representing work status of the day:
            - `True` **IF IT'S A HOLIDAY** but the day is not at weekend
            - `False` if day is at weekend, but it's a working day
    :param date: date to check
    :type date: datetime.timedelta
    :return: True if date is work day, False if it isn't
    :rtype: bool
    """

    date_iso = date.isoformat() if type(date) == date_type else date.date().isoformat()
    return (
        date.weekday() in [5, 6] and  # date's weekday is Saturday or Sunday
        WORKING_DAYS.get(date_iso, True) or  # but it's not a holiday
        WORKING_DAYS.get(date_iso, False)  # or date in't at weekend, but it's holiday
    )


def get_accelerator(context):
    """Checks if some accelerator attribute was set and returns it

    `calculate_business_date` is used not only by auctions as a `context`,
    but also with other models. This method recognizes accelerator attribute
    for the `context` model if it present in `possible_attributes` below.
    """
    if not context:
        return
    possible_attributes = (
        'procurementMethodDetails',
        'sandboxParameters',
    )
    accelerator = None
    for attr in possible_attributes:
        if isinstance(context, dict) and context.get(attr):
            accelerator = context[attr]
            break
        elif hasattr(context, attr):
            accelerator = getattr(context, attr)
            break
    if accelerator and isinstance(accelerator, basestring):
        return accelerator


def accelerated_calculate_business_date(date, period, accelerator, specific_time=None, specific_hour=None):
    re_obj = ACCELERATOR_RE.search(accelerator)
    if re_obj and 'accelerator' in re_obj.groupdict():
        if specific_hour or specific_time:
            period = period + (specific_time_setting(date, specific_time, specific_hour) - date)
        return date + (period / int(re_obj.groupdict()['accelerator']))


def jump_working_days(time_cursor, days_to_jump, reverse_calculations):
    while days_to_jump > 0:
        time_cursor = jump_closest_working_day(time_cursor, backward=reverse_calculations)
        days_to_jump -= 1
    return time_cursor


def validate_jump_length(days_to_jump):
    if days_to_jump == 0:
        raise ValueError("delta.days must be not equal to zero")


def operate_on_last_working_day(time_cursor, start_is_holiday, specific_hour, reverse_calculations):
    if start_is_holiday and not specific_hour:
        time_cursor = round_out_day(time_cursor, reverse_calculations)
    return time_cursor


def working_days_calculation(time_cursor, days_to_jump, specific_hour, start_is_holiday, reverse_calculations):
    validate_jump_length(days_to_jump)

    time_cursor = jump_working_days(time_cursor, days_to_jump, reverse_calculations)

    return operate_on_last_working_day(time_cursor, start_is_holiday, specific_hour, reverse_calculations)


def calculate_business_date(start, delta, context, working_days=False, specific_hour=None, **kwargs):
    """This method calculates end of business period from given start and timedelta

    The calculation of end of business period is complex, so this method is used project-wide.
    Also this method provides support of accelerated calculation, useful while testing.

    The end of the period is calculated **exclusively**, for example:
        Let the 1-5 days of month (e.g. September 2008) be working days.
        So, when the calculation will be initialized with following params:

            start = datetime(2008, 9, 1)
            delta = timedelta(days=2)
            working_days = True

        The result will be equal to `datetime(2008, 9, 3)`.

    :param start: the start of period
    :param delta: duration of the period
    :param context: object, that holds data related to particular business process,
        usually it's Auction model's instance. Must be present to use acceleration
        mode.
    :param working_days: make calculations taking into account working days
    :param specific_hour: specific hour, to which date of period end should be rounded
    :kw param result_is_working_day: if specified, result of calculations always be working day,
        even if working_days = False. In this case result may differ from needed calendar days
        because of working day adjustment.
    :type start: datetime.datetime
    :type delta: datetime.timedelta
    :type context: openprocurement.api.models.Tender
    :type working_days: bool
    :return: the end of period
    :rtype: datetime.datetime

    """

    time_cursor = copy(start)
    start_is_holiday = is_holiday(start)
    accelerator = get_accelerator(context)
    reverse_calculations = delta < timedelta()
    days_to_jump = abs(delta.days)
    specific_time = kwargs.get('specific_time')
    result = None

    tz = getattr(start, 'tzinfo', None)
    naive_calculations = tz is None
    date_calculations = type(start) == date_type
    skip_tz_converting = naive_calculations or date_calculations

    time_cursor = time_cursor if skip_tz_converting else time_cursor.astimezone(utc)

    if accelerator:
        result = accelerated_calculate_business_date(time_cursor, delta, accelerator, specific_time, specific_hour)
    if not working_days and result is None:
        result = time_cursor + delta
    if working_days and result is None:
        result = working_days_calculation(
            time_cursor, days_to_jump, specific_hour, start_is_holiday, reverse_calculations
        )

    time_cursor = result if skip_tz_converting else result.astimezone(tz)

    if kwargs.get('result_is_working_day') and is_holiday(time_cursor):
        time_cursor = jump_closest_working_day(time_cursor, backward=reverse_calculations)

    if not accelerator:
        time_cursor = specific_time_setting(time_cursor, specific_time, specific_hour)

    return time_cursor


def utcoffset_is_aliquot_to_hours(dt):
    offset_seconds = dt.utcoffset().total_seconds()
    seconds_overlap = offset_seconds % SECONDS_IN_HOUR
    if seconds_overlap == 0:
        return True
    return False


def utcoffset_difference(dt, tz=TZ):
    """
    Compute difference between datetime in it's own UTC offset
    and it's offset in another timezone with equal date and time values

    This tool is suited for checking if some datetime corresponds
    to some timezone in future or past.

    Returns tuple, where:
        0: difference between dt with it's own utcoffset and dt in another timezone
        1: target timezone's utcoffset in dt's time
    """
    utcoffset_dt = dt.utcoffset().total_seconds()
    utcoffset_dt_hours = utcoffset_dt / SECONDS_IN_HOUR

    dt_in_server_tz = set_timezone(dt, tz)
    utcoffset_in_server_tz = dt_in_server_tz.utcoffset().total_seconds()
    utcoffset_in_server_tz_hours = round_seconds_to_hours(utcoffset_in_server_tz)

    difference = utcoffset_dt_hours - utcoffset_in_server_tz_hours

    return (difference, utcoffset_in_server_tz_hours)


def time_dependent_value(border_date, before, after):
    if get_now() >= border_date:
        return after
    return before
