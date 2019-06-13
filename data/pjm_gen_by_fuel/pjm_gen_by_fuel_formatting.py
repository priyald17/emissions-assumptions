import argparse
import os
import pandas as pd
from datetime import timedelta

'''
    Get formatted PJM hourly generation by fuel.
    Input: Hourly generation by fuel, downloaded from PJM DataMiner2 (for RTO region).
        Link: https://dataminer2.pjm.com/feed/gen_by_fuel/definition
    Output: Clean hourly generation-by-fuel data.
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', default='formatted_data', 
        help='save folder path')
    parser.add_argument('--endYear', type=int, default=2017)
    args = parser.parse_args()

    # Read in and format generation data
    print('getting pjm generation data')
    df = pd.read_csv(os.path.join('raw_data', 'gen_by_fuel.csv'), index_col=0, parse_dates=[0])
    df.drop('datetime_beginning_ept', axis=1, inplace=True)
    df.index.names = ['DATE_UTC']
    df.index = df.index + timedelta(hours=-5)  # TODO: currently dates are actually UTC-5
    df = df.sort_index()
    df.columns = ['FUEL_TYPE', 'Generation (MW)', 'PERCENT_TOTAL', 'IS_RENEWABLE']

    # 2016 is first full year with clean data
    df = pd.DataFrame(df.loc['2016-01-01':])


    print('formatting data')
    # Drop zeros in data
    totals = df.groupby(df.index).sum()
    df = df.drop(totals[totals['Generation (MW)'] == 0].index)

    # Percentages don't all sum to 100% (though they're all close), so we'll scale them
    gen_scaled = \
        df.groupby(df.index).apply(lambda x: x['Generation (MW)']/(x['PERCENT_TOTAL'].sum()))
    pct_scaled = \
        df.groupby(df.index).apply(lambda x: x['PERCENT_TOTAL']/(x['PERCENT_TOTAL'].sum()))
    gen_scaled.index = df.index
    pct_scaled.index = df.index
    df['Generation (MW)'] = gen_scaled
    df['PERCENT_TOTAL']   = pct_scaled

    # Reindex for all hours and dates
    df = df.set_index([df.index, 'FUEL_TYPE'])
    date_range = pd.date_range(
        start='2016-01-01 05:00', end='{}-01-01 5:00'.format(args.endYear + 1), freq='H')
    fuel_types = df.index.get_level_values('FUEL_TYPE').unique()
    multi_idx = pd.MultiIndex.from_product(
        [date_range, fuel_types], names=['DATE_UTC', 'FUEL_TYPE'])
    df = df.reindex(multi_idx).sort_index()

    # Convert formatting so there is one row associated with each hour, 
    #   and columns indicate marginal fuel proportions
    df_wide = df.reset_index().set_index('DATE_UTC')
    df_wide = pd.get_dummies(df_wide['FUEL_TYPE']).multiply(
        df_wide['Generation (MW)'], axis=0)
    # Sum all vectors belonging to the same date (and treat all nans as nan)
    df_wide = df_wide.groupby(df_wide.index).sum(min_count=1)
    
    # Save data
    print('saving data')
    save = args.save
    if not os.path.exists(save): os.makedirs(save)
    df.to_csv(os.path.join(save, 'pjm_gen_by_fuel_type.csv'))
    df_wide.to_csv(os.path.join(save, 'pjm_gen_by_fuel_type_wide.csv'))


if __name__=='__main__':
    main()