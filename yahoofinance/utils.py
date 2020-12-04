import locale
import calendar
import numpy as np
from pytz import timezone as pytz
from datetime import datetime, timedelta


locale.setlocale(locale.LC_ALL, '')
_unix_epoch = datetime(1970, 1, 1, tzinfo=pytz('UTC'))
_business_calender = calendar.Calendar(firstweekday=calendar.MONDAY)


def UT_to_str(time, timezone='UTC', fmt='%Y-%m-%d %H:%M:%S %Z',
              epoch=_unix_epoch):
    """
    Arguments:
        time: time in seconds since epoch
    
    Keyword arguments:
        timezone: one of the pytz timezones (default: UTC)
        fmt: how time string is formatted (default: %Y-%m-%d %H:%M:%S %Z)
        epoch: when t=0 (default: unix, 1970-01-01 00:00:00 UTC)

    Examples:
        UT_to_str(345459600, timezone='America/New_York')
        UT_to_str(1577865600, timezone='US/Eastern')

    Returns:
        String of date
    """
    if type(time) is list:
        date = []
        for t in time:
            unix_time = epoch + timedelta(seconds=t)
            date.append(unix_time.astimezone(tz=pytz(timezone)).strftime(fmt))
        return date
    unix_time = epoch + timedelta(seconds=time)
    return unix_time.astimezone(tz=pytz(timezone)).strftime(fmt)


def str_to_UT(time, timezone='UTC', fmt='%Y-%m-%d %H:%M:%S',
              epoch=_unix_epoch):
    """
    Arguments:
        time: string to be convert to epoch time

    Keyword argumens:
        timezone: one of the pytz timezones (default: UTC)
        fmt: how time string is formatted (default: %Y-%m-%d %H:%M:%S)
        epoch: when t=0 in UTC (default: 1970-01-01)

    Example:
        str_to_UT('2020-01-01 00:00:00', timezone='US/Pacific')

    Returns:
        Integer number of seconds since epoch
    """
    tz = pytz(timezone)
    time = tz.localize(datetime.strptime(time, fmt))
    return int((time-epoch).total_seconds())



def UT_to_FTDM_UT(time, timezone='UTC', epoch=_unix_epoch):
    """
    Description:
        Calculates the seconds since epoch of the first trading day of the
        month (FTDM), taking into account the New Years Days trading holiday
        
    Arguments:
        time: seconds since epoch (in seconds)
        
    Keyword arguments:
        timezone:
        epoch:
        
    Returns:
        Time since epoch of first trading day of the month
    """
    year, month = list(map(int, UT_to_str(time, fmt='%Y %m',
                                          timezone=timezone, epoch=epoch)
                                .split()))
    cal = _business_calender.monthdayscalendar(year, month)
    # Sum days in first business week, in general three cases exist for FTM
    week1_sum = np.sum(cal[0])
    FTDM = 3 if (week1_sum == 3) else 2 if (week1_sum == 1) else 1
    # Account for New Years Day
    if FTDM == 1 and month == 1:
        # Special case when 01-01 falls on a Friday, FTM is 4
        if week1_sum == 6:
            FTDM = 4
        else:
            FTDM += 1
    return (pytz(timezone).localize(datetime(year, month, FTDM))
            -epoch).total_seconds()