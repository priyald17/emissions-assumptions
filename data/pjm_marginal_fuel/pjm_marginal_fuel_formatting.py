import argparse
import os
import re
import pandas as pd
from datetime import datetime, timedelta

os.sys.path.insert(0, os.path.dirname(os.getcwd()))
import date_helpers

'''
    Get formatted PJM hourly marginal fuel proportions.
    Input: Hourly marginal generator proportions by fuel type, from PJM.
        Link: http://www.monitoringanalytics.com/data/marginal_fuel.shtml
    Output: Clean hourly generation-by-fuel data.
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', default='formatted_data', 
        help='save folder path')
    parser.add_argument('--startYear', type=int, default=2016)
    parser.add_argument('--endYear', type=int, default=2017)
    args = parser.parse_args()

    # Read in and format marginal fuel proportions data
    print('getting pjm marginal fuel proportions data')

    # Some fuels have different names from year to year. Construct a mapping.
    fuel_renaming_dict = \
        {'Lfg': 'Land Fill Gas', 'Miscellaneous': 'Misc', 'Msw': 'Municipal Waste'}

    # Read in and format data
    have_created_full_df = False
    for year in range(args.startYear, args.endYear+1):
        print(year)
        for month in range(1, 13):
            filepath = os.path.join(
                'raw_data', str(year), '{0:}{1:02d}_Marginal_Fuel_Postings.csv'.format(year, month))
            df = pd.read_csv(
                filepath, index_col=0, parse_dates=[0], usecols=[0,1,2,3], date_parser=date_parser)
            df.columns = ['tz', 'FUEL_TYPE', 'PERCENT_MARGINAL']
            
            # In case we're given percentages (as in some years), convert to proportions.
            df['PERCENT_MARGINAL'] = df['PERCENT_MARGINAL'].map(convert_percent)
            
            # Standardize fuel type names across years (title case and consistent naming)
            df['FUEL_TYPE'] = df['FUEL_TYPE'].map(lambda x: x.lower().title())
            # Get renaming if it exists, otherwise return the existing string
            df['FUEL_TYPE'] = df['FUEL_TYPE'].map(lambda x: fuel_renaming_dict.get(x, x))
        
            if have_created_full_df:
                marg_fuels = pd.concat([marg_fuels, df], axis=0)
            else:
                marg_fuels = df.copy()
                have_created_full_df = True

    print('formatting data')
    # Convert dates to UTC
    marg_fuels = date_helpers.get_df_dates_tz_to_utc(marg_fuels)
    marg_fuels.drop('tz', axis=1, inplace=True)
    # TODO: currently dates are actually UTC-5
    marg_fuels.index = marg_fuels.index + timedelta(hours=-5) 

    # Convert formatting so there is one row associated with each hour, 
    #   and columns indicate marginal fuel proportions
    marg_fuels = pd.get_dummies(marg_fuels['FUEL_TYPE']).multiply(
        marg_fuels['PERCENT_MARGINAL'], axis=0)
    # Sum all vectors belonging to the same date
    marg_fuels = marg_fuels.groupby(marg_fuels.index).sum()

    # Ensure that proportions for each hour sum to 1
    sums = marg_fuels.sum(axis=1)
    marg_fuels = marg_fuels.divide(sums, axis=0)
    

    # Save data
    print('saving data')
    save = args.save
    if not os.path.exists(save): os.makedirs(save)
    marg_fuels.to_csv(os.path.join(save, 'marginal_fuels.csv'))


# Files have a nonstandard date format, so specify format
def date_parser(key):
    # Try both different datetime formats the raw data files use.
    try:
        dt = datetime.strptime(key, '%d%b%Y:%H:%M:%S')
    except ValueError:
        dt = datetime.strptime(key, '%d%b%y:%H:%M:%S')
    return dt

# If input value is a percentage, convert to proportion.
def convert_percent(value):
    matching = re.compile('(\d+.\d+)%').match(str(value))
    return float(matching.group(1))/100 if matching else value




if __name__=='__main__':
    main()