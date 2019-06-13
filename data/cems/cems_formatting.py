import argparse
import os
import pandas as pd
import numpy as np

'''
    Get clean aggregated hourly generation/emissions and the associated generation/emissions
        differences between hours.
    Input: Aggregated hourly data from CEMS. This data was obtained from EPA CEMS and then 
        aggregated by RTO/ISO or NERC region.
    Output: Clean aggregated hourly data, and differenced hourly data.
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aggRegion', choices=['isorto', 'nerc'], required=True,
        help='region type to which data should be aggregated')
    parser.add_argument('--save', default='formatted_data', 
        help='save folder path')
    parser.add_argument('--startYear', type=int, default=2006)
    parser.add_argument('--endYear', type=int, default=2017)
    args = parser.parse_args()

    agg_region = args.aggRegion

    # Read in CEMS data, aggregated by region. Drop rows without region label.
    print('getting emissions data')
    emissions = pd.read_csv(
        os.path.join('raw_data', 'emit_agg_by_{}.csv'.format(agg_region)))
    emissions = emissions[pd.notnull(emissions[agg_region])]

    # Convert timestamp to datetime
    #  TODO: The time is actually UTC-5, not UTC. Need to change column name.
    emissions['ts'] = pd.to_datetime(emissions['ts'])

    # Organize by timestamp and region
    emissions = emissions.set_index(['ts', agg_region]).sort_index()
    emissions.index.names = ['DATE_UTC', agg_region]

    # Convert units to kg
    KG_IN_LB = 0.453592
    KG_IN_TON = 907.185
    emissions = convert_to_kg(emissions, 'lbs', KG_IN_LB)
    emissions = convert_to_kg(emissions, 'tons', KG_IN_TON)

    # Get differenced data, and format columns
    print('getting differenced data')
    diffs = get_diffs(emissions, agg_region, args.startYear, args.endYear)
    # diffs.columns = diffs.columns.map(lambda x: '{}-diffs'.format(x))

    # Save data
    print('saving data')
    save = args.save
    if not os.path.exists(save): os.makedirs(save)
    emissions.to_csv(os.path.join(save, 'cems_{}.csv'.format(agg_region)))
    diffs.to_csv(os.path.join(save, 'cems_diffs_{}.csv'.format(agg_region)))



def convert_to_kg(df, unit_label, conversion_factor):
    old_unit_cols = [x for x in df.columns if unit_label in x]
    df[old_unit_cols] = df[old_unit_cols] * conversion_factor
    df.columns = [x.replace(unit_label, 'kg') for x in df.columns]
    return df


# Note: df must be indexed by date and aggregation region
def get_diffs(df, agg_region, start_year, end_year):

    # Reindex to ensure all hours and regions are represented
    all_hours = pd.date_range(
        start='{}-01-01'.format(start_year), end='{}-01-01'.format(end_year+1), freq='H')
    all_hours_multidx = pd.MultiIndex.from_product(
        [all_hours, df.index.get_level_values(agg_region).unique()], 
        names=['DATE_UTC', agg_region])
    df = df.reindex(all_hours_multidx)

    # Sort index by region and then date
    df = df.reset_index().set_index([agg_region, 'DATE_UTC']).sort_index()

    # Take diffs and correct "spillover" between boundaries of regions
    diffs = df.diff().reset_index()
    mask = diffs[agg_region] != diffs[agg_region].shift(1)
    diffs[mask] = np.nan

    # Rearrange back to being sorted by date, then region
    diffs = diffs.set_index(['DATE_UTC', agg_region]).sort_index()

    # Drop any null diffs
    diffs = diffs.dropna(how='all')

    return diffs



if __name__=='__main__':
    main()
