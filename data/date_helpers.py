#/usr/bin/env python3

###############################################################################
# Helper functions for managing dates and time zones.
###############################################################################

import pandas as pd
from datetime import datetime, timedelta
import pytz
import numpy as np

def get_df_dates_to_utc(df):
    '''Converts datetime index of data frame from Eastern to UTC.

    Note: pytz's localization function is a bit faulty during the EDT --> EST
    daylight savings transition (the time zone changes at the wrong hour), so
    this function is best-suited for situations where some off-by-one errors 
    are not a problem during the daylight savings transition day.
    If off-by-one errors matter, use get_df_dates_tz_to_utc.

    Args:
        df: Pandas data frame with naive datetime index in eastern time.

    Returns:
        Input data frame with datetime index converted to UTC.
    '''

    # Ensure we don't modify the passed-in df
    df = df.copy()

    # Add time zone to dates
    eastern = pytz.timezone('US/Eastern')
    df['with_tz'] = df.index.map(lambda x: eastern.localize(x))
    
    # Convert to UTC
    df['DATE_UTC'] = df['with_tz'].map(lambda x: x.astimezone(pytz.utc))
    
    # Reorganize data frame
    df.set_index('DATE_UTC', inplace=True)
    df.drop('with_tz', axis=1, inplace=True)
    return df    

def get_df_dates_tz_to_utc(df):
    '''Creates version of data frame with datetime index in UTC.

    Note: This function was developed to fix some issues with pytz's default
    localization. To use it, you must first create a column in the data frame
    with time zone information.

    Args:
        df: Pandas data frame with index containing naive datetimes
          and a 'tz' column indicating the time zone (EST or EDT)

    Returns:
        Input data frame with datetime index converted to UTC.
    '''

    # Ensure we don't modify the passed-in df
    df = df.copy()
    
    # Make date a normal column so we can add tzinfo
    df.index.name = 'DATE'
    df.reset_index(inplace=True)
    
    # Add time zone to dates
    get_offset = lambda tz: pytz.FixedOffset(-300 if tz == 'EST' else -240)
    df['with_tz'] = df.apply(lambda row: get_offset(row['tz']).localize(row['DATE']),
                             axis=1)
    
    # Convert to UTC
    df['DATE_UTC'] = df['with_tz'].map(lambda x: x.astimezone(pytz.utc))

    # Reorganize data frame
    df.set_index('DATE_UTC', inplace=True)
    df.drop(['DATE', 'with_tz'], axis=1, inplace=True)
    return df


def get_tz_name(date_val, hr_val):
    '''Get time zone given date and hour.

    Note: This function was created to deal with some bugs in default 
    pytz localization.

    Args:
        date_val: Datetime with correct year, month, and day values.
        hr_val: Hour value.

    Returns:
        Name of correct time zone (EST or EDT).
    '''

    # Get previous hour value, giving user the option to store fractional
    #  hours when hour is ambiguous during EDT --> EST transition.
    #  E.g. during the EDT --> EST transition, there are two 1ams.
    #    For 1am EDT (stored as hr_val = 1), prev_hour = 0.
    #    For 1am EST (stored as hr_val = 1.5), prev_hour = 1.
    prev_hour = max(0, int(np.floor(hr_val-0.5)))

    # Localize and get time zones for (prev_hour):59 and (curr_hour):00
    dt_59 = datetime(date_val.year, date_val.month, date_val.day,
                    hour=prev_hour, minute=59)
    dt_00 = dt_59 + timedelta(minutes=1)                                    
    
    eastern = pytz.timezone('US/Eastern')
    dt_minus_one = eastern.localize(dt_59)
    dt_orig_hr = eastern.localize(dt_00)

    minus_tz = dt_minus_one.tzinfo.tzname(dt_minus_one)
    orig_tz  = dt_orig_hr.tzinfo.tzname(dt_orig_hr)
    
    # Figure out actual time zone
    if (minus_tz != orig_tz and dt_orig_hr.hour == 3):
        # If time zone transitioned and it's 3am, we're in EST --> EDT.
        #  The EDT localization is correct.
        return orig_tz
    else:
        # In EDT --> EST case, the (prev_hour):59 localization is correct.
        # If no transition, we can return either tz.
        return minus_tz 

month_to_season = ['winter'] * 3 + ['trans'] + ['summer'] * 5 + ['trans'] + ['winter'] * 2
def add_season(df):
    '''Given DataFrame with datetime index, label season.

    Args: 
        df: DataFrame with datetime index

    Returns:
        Copy of df with season column added
    '''
    df_out = pd.DataFrame(df)
    df_out['season'] = df_out.index.map(lambda x: month_to_season[x.month - 1])
    return df_out