# -*- coding: utf-8 -*-
import iso8601
import unittest

from datetime import timedelta, datetime, date, time
from pytz import timezone, utc

from openprocurement.api.utils.timestuff import (
    calculate_business_date,
    round_seconds_to_hours,
    set_timezone,
    utcoffset_difference,
    utcoffset_is_aliquot_to_hours,
    time_dependent_value
)
from openprocurement.api.utils.common import (
    get_now,
)


class CalculateBusinessDateTestCase(unittest.TestCase):

    def test_accelerated_calculation(self):
        # auction = auction_mock(procurementMethodDetails='quick, accelerator=1440') # TODO: Fix mocked attr
        auction = {"procurementMethodDetails": 'quick, accelerator=1440'}
        start = get_now()
        period_to_add = timedelta(days=1440)
        result = calculate_business_date(start, period_to_add, auction)
        self.assertEqual((result - start).days, 1)

    def test_accelerated_calculation_specific_hour(self):
        # auction = auction_mock(procurementMethodDetails='quick, accelerator=1440') # TODO: Fix mocked attr
        auction = {"procurementMethodDetails": 'quick, accelerator=1440'}
        start = datetime(2018, 4, 2, 16)
        specific_hour = start.hour + 2
        period_to_add = timedelta(days=20)
        result = calculate_business_date(start, period_to_add, auction, specific_hour=specific_hour)
        target_seconds = 20*60+5
        self.assertEqual((result - start).seconds, target_seconds)

    def test_accelerated_calculation_specific_time(self):
        auction = {"procurementMethodDetails": 'quick, accelerator=1440'}
        start = datetime(2018, 4, 2, 16)
        specific_time = time(18, 30)
        period_to_add = timedelta(days=20)
        result = calculate_business_date(start, period_to_add, auction, specific_time=specific_time)
        target_seconds = 20*60+6
        self.assertEqual((result - start).seconds, target_seconds)

    def test_common_calculation_with_working_days(self):
        """This test assumes that <Mon 2018-4-9> is holiday, besides regular holidays
        of that month. It must be fixed in `working_days.json` file, that translates
        into `WORKING_DAYS` constant.
        """
        start = datetime(2018, 4, 2)
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17)
        result = calculate_business_date(start, business_days_to_add, None, working_days=True)

        self.assertEqual(result, target_end_of_period)

    def test_common_calculation_with_working_days_working_end(self):
        start = datetime(2018, 10, 11)
        business_days_to_add = timedelta(days=3)
        target_end_of_period = datetime(2018, 10, 17)
        result = calculate_business_date(start, business_days_to_add, None, working_days=True)

        self.assertEqual(result, target_end_of_period)

    def test_common_calculation_with_working_days_specific_hour(self):
        """This test assumes that <Mon 2018-4-9> is holiday, besides regular holidays
        of that month. It must be fixed in `working_days.json` file, that translates
        into `WORKING_DAYS` constant.
        """
        start = datetime(2018, 4, 2)
        specific_hour = 18
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17)
        result = calculate_business_date(
            start, business_days_to_add, None, working_days=True, specific_hour=specific_hour
        )

        self.assertEqual(result, target_end_of_period + timedelta(hours=specific_hour))

    def test_calculate_with_negative_time_period(self):
        start = datetime(2018, 4, 17)
        business_days_to_add = timedelta(days=-10)
        target_end_of_period = datetime(2018, 4, 2)
        result = calculate_business_date(start, business_days_to_add, None, working_days=True)

        self.assertEqual(result, target_end_of_period)

    def test_start_is_holiday_specific_hour_none(self):
        start = datetime(2000, 5, 6, 13, 22)  # Saturday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 9, 0, 0)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_start_is_holiday_specific_hour_set(self):
        start = datetime(2000, 5, 6, 20, 22)  # Saturday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 8, 18, 0)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=18)

        self.assertEqual(result, target_end)

    def test_start_is_holiday_specific_hour_set_with_tz(self):
        TARGET_HOUR = 18

        tzone = timezone('Europe/Kiev')
        start = datetime(2018, 5, 6, 20, 22, tzinfo=tzone)  # Saturday
        days_to_add = timedelta(days=1)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=TARGET_HOUR)

        self.assertEqual(result.hour, TARGET_HOUR)

    def test_start_is_not_holiday_specific_hour_none(self):
        start = datetime(2000, 5, 5, 20, 22)  # Friday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 8, 20, 22)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_start_is_not_holiday_specific_hour_set(self):
        start = datetime(2000, 5, 5, 20, 22)  # Friday
        days_to_add = timedelta(days=1)
        target_end = datetime(2000, 5, 8, 18, 0)

        result = calculate_business_date(start, days_to_add, None, working_days=True, specific_hour=18)

        self.assertEqual(result, target_end)

    def test_reverse_start_is_not_holiday_specific_hour_not_set(self):
        start = datetime(2018, 7, 20, 17, 15)
        days_to_substract = timedelta(days=-4)
        target_end = datetime(2018, 7, 16, 17, 15)

        result = calculate_business_date(start, days_to_substract, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_reverse_start_is_not_holiday_specific_hour_not_set_one_day(self):
        start = datetime(2018, 7, 20)
        days_to_substract = timedelta(days=-1)
        target_end = datetime(2018, 7, 19)

        result = calculate_business_date(start, days_to_substract, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_start_is_not_holiday_specific_hour_not_set_one_day(self):
        start = datetime(2018, 7, 20)
        days_to_substract = timedelta(days=1)
        target_end = datetime(2018, 7, 23)

        result = calculate_business_date(start, days_to_substract, None, working_days=True, specific_hour=None)

        self.assertEqual(result, target_end)

    def test_result_is_working_day(self):
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=3)
        target_end = datetime(2000, 5, 8)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_no_need_to_add_wd(self):
        """There isn't a need to add a working day if result is already working day"""
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=2)
        target_end = datetime(2000, 5, 5)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_unintended_jump(self):
        """Unintended holiday jump bug

        If timezone converting changes date, jumps when `result_is_working_day`==True`
        can overlap and cause error by adding wrong amount of days.
        """
        start = iso8601.parse_date('2018-12-19T00:00:00+02:00')
        days_to_add = timedelta(days=60)
        target_end = iso8601.parse_date('2019-02-18T18:00:00+02:00')

        result = calculate_business_date(start, days_to_add, None, specific_hour=18, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_with_specific_hour(self):
        start = datetime(2000, 5, 3, 15, 0)  # Wednesday
        days_to_add = timedelta(days=3)
        target_end = datetime(2000, 5, 8, 18, 0)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True, specific_hour=18)

        self.assertEqual(result, target_end)

    def test_result_is_working_day_reverse(self):
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=-3)
        target_end = datetime(2000, 4, 28)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)

    def test_result_timezone_aware(self):
        tzone = timezone('Europe/Kiev')
        start = tzone.localize(datetime(2018, 10, 20))
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(str(start.utcoffset()), '3:00:00')
        self.assertEqual(str(result.utcoffset()), '2:00:00')

    def test_result_timezone_naive(self):
        start = datetime(2018, 10, 20)
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertIsNone(start.utcoffset())
        self.assertIsNone(result.utcoffset())

    def test_date_add_days(self):
        start = datetime(2018, 10, 20).date()
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)
        target_end = date(2018, 11, 9)

        result = calculate_business_date(start, days_to_add, None, result_is_working_day=True)

        self.assertEqual(result, target_end)
        self.assertEqual(type(result), type(target_end))

    def test_kwargs(self):
        start = datetime(2018, 10, 20).date()
        # 28.10 `Europe/Kiev` timezone moves to DST
        days_to_add = timedelta(days=20)
        target_end = date(2018, 11, 9)

        result = calculate_business_date(
            start=start,
            delta=days_to_add,
            context=None,
            result_is_working_day=True
        )

        self.assertEqual(result, target_end)
        self.assertEqual(type(result), type(target_end))

    def test_zero_length_delta_working_days(self):
        start = datetime(2000, 5, 3)  # Wednesday
        days_to_add = timedelta(days=0)

        with self.assertRaises(ValueError):
            calculate_business_date(start, days_to_add, None, working_days=True, result_is_working_day=True)

    def test_common_calculation_with_working_days_specific_time(self):
        start = datetime(2018, 4, 2)
        specific_time = time(18, 4)
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17, 18, 4)
        result = calculate_business_date(
            start, business_days_to_add, None, working_days=True, specific_time=specific_time
        )

        self.assertEqual(result, target_end_of_period)

    def test_common_calculation_with_working_days_specific_time_priority(self):
        """Test `specific_time` kwarg priority over `specific_hour` one"""
        start = datetime(2018, 4, 2)
        specific_time = time(18, 4)
        business_days_to_add = timedelta(days=10)
        target_end_of_period = datetime(2018, 4, 17, 18, 4)
        result = calculate_business_date(
            start, business_days_to_add, None, working_days=True, specific_time=specific_time, specific_hour=18
        )

        self.assertEqual(result, target_end_of_period)


class RoundSecondsToHoursTestCase(unittest.TestCase):

    def test_round_down(self):
        seconds = 18010.0  # 5 hours 10 seconds
        hours = 5
        res = round_seconds_to_hours(seconds)

        self.assertEqual(hours, res)

    def test_round_up(self):
        seconds = 17099  # 4 hours 59 seconds
        hours = 5
        res = round_seconds_to_hours(seconds)

        self.assertEqual(hours, res)

    def test_seconds_are_aliquot_to_hours(self):
        seconds = 18000  # 4 hours 59 seconds
        hours = 5
        res = round_seconds_to_hours(seconds)

        self.assertEqual(hours, res)


class SetTimezoneTestCase(unittest.TestCase):

    def test_only_timezone_has_changed(self):
        kyiv_tz = timezone('Europe/Kiev')
        d_in = datetime.now(kyiv_tz)
        res = set_timezone(d_in, utc)
        self.assertEqual(d_in.hour, res.hour)
        self.assertNotEqual(res.tzinfo, None, 'tzinfo must be present')


class UtcoffsetIsAliquotToHoursTestCase(unittest.TestCase):

    def test_is_not_aliquot(self):
        dt = iso8601.parse_date('2018-12-21T13:11:36+05:03')

        res = utcoffset_is_aliquot_to_hours(dt)

        self.assertEqual(res, False, 'offset is not aliquot to hours')

    def test_is_aliquot(self):
        dt = iso8601.parse_date('2018-12-21T13:11:36+05:00')

        res = utcoffset_is_aliquot_to_hours(dt)

        self.assertTrue(res, 'offset is aliquot to hours')


class UtcoffsetDifferenceTestCase(unittest.TestCase):

    def test_difference_is_present(self):
        tstamp = '2018-12-22T15:49:17.787628+03:00'
        dt = iso8601.parse_date(tstamp)
        target_res = (1, 2)

        res = utcoffset_difference(dt)

        self.assertEqual(res, target_res)

    def test_difference_is_none(self):
        tstamp = '2018-12-22T15:49:17.787628+02:00'
        dt = iso8601.parse_date(tstamp)
        target_res = (0, 2)

        res = utcoffset_difference(dt)

        self.assertEqual(res, target_res)

    def test_difference_is_present_and_negative(self):
        tstamp = '2018-12-22T15:49:17.787628+01:00'
        dt = iso8601.parse_date(tstamp)
        target_res = (-1, 2)

        res = utcoffset_difference(dt)

        self.assertEqual(res, target_res)


class TimeDependentValueTestCase(unittest.TestCase):

    def test_when_get_now_before(self):
        now = get_now()
        border_date = now - timedelta(days=10)
        before = 'before'
        after = 'after'

        # Should appear `after` value because current date is after border_date
        value = time_dependent_value(border_date, before, after)
        self.assertEqual(value, after)

    def test_when_get_now_after(self):
        now = get_now()
        border_date = now + timedelta(days=10)
        before = 'before'
        after = 'after'

        # Should appear `before` value because current date is before border_date
        value = time_dependent_value(border_date, before, after)
        self.assertEqual(value, before)

    def test_when_compared_date_passed(self):
        now = get_now()
        border_date = now - timedelta(days=2)
        compared_date = now - timedelta(days=10)
        before = 'before'
        after = 'after'

        # Should appear `before` value because compared date is before border_date
        value = time_dependent_value(border_date, before, after, compared_date=compared_date)
        self.assertEqual(value, before)
