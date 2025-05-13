import calendar
import datetime

import pytz
from django.utils import timezone
import dateutil.parser
from dateutil.relativedelta import relativedelta
from django.utils import dateparse
import holidays


def validate(datetime_str):
    try:
        dateutil.parser.parse(datetime_str)
        return True
    except ValueError:
        raise Exception("Please enter a valid datetime in format 'YYYY-MM-DDTHH:mm'")


def format_string(date_string, current_format="%Y-%m-%d", new_format="%A, %B %e, %Y"):
    return datetime.datetime.strptime(date_string,  current_format).strftime(new_format)


def format(date, new_format="%d/%m/%Y, %H:%M %Z"):
    return date.strftime(new_format).replace('{S}', str(date.day) + suffix(date.day))


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def parse(datetime_str, return_date=False):
    datetime_ = dateutil.parser.parse(datetime_str)

    if not return_date:
        return datetime_

    return datetime_.date()


def create_date(day_, month, year):
    return datetime.date(year=year, month=month, day=day_)


def day(date_):
    return date_.strftime('%A')


def now():
    return timezone.now()


def today():
    return now().today()


def tomorrow():
    return days_later(day_count=1)


def yesterday():
    return days_ago(1)


def days_ago(days, date=None):
    from datetime import timedelta
    if not date:
        date = timezone.now()
    return date - timedelta(days=days)


def days_later(date=None, day_count=1):
    if not date:
        date = today()

    return date + datetime.timedelta(days=day_count)


def months_ago(months, date=None):

    if not date:
        date = timezone.now()
    return date - relativedelta(months=months)


def months_later(months):
    from dateutil.relativedelta import relativedelta
    return timezone.now() + relativedelta(months=months)


def start_of_month(date):
    return date.replace(day=1)


def end_of_month(date):
    last_day_of_month = calendar.monthrange(date.year, date.month)[1]
    return create_date(last_day_of_month, date.month, date.year)


def start_of_current_month():
    _start_of_current_month = start_of_month(today().date())
    return _start_of_current_month


def end_of_current_month():
    _end_of_current_month = end_of_month(today().date())
    return _end_of_current_month


def is_holiday(date_, country="IE"):
    ireland_holidays = holidays.country_holidays(country)

    is_weekend = date_.weekday() >= 5

    return is_weekend or date_ in ireland_holidays


def days_ago_excluding_holidays(day_count, date_):
    count = 0
    while count < day_count:
        date_ = days_ago(1, date_)

        if not is_holiday(date_):
            count += 1

    return date_





