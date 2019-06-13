import argparse
import os
import pandas as pd
import numpy as np
from datetime import datetime
from plot_intervention import plot_total_damages, get_stacked_plot

LABELS = ['so2_kg', 'nox_kg', 'pm25_kg', 'co2_kg', 'so2_dam_ap2', 'nox_dam_ap2',
       'pm25_dam_ap2', 'so2_dam_eas', 'nox_dam_eas', 'pm25_dam_eas',
       'co2_dam', 'dam_ap2', 'dam_eas']
LABELS.sort()

GROUPING_NAMES = ['SeasonalTOD', 'MonthTOD', 'TOD', 'YearOnly', 'Month', 'Hour']
GROUPING_COLS = [['year', 'season', 'hour'], ['year', 'month', 'hour'], 
        ['year', 'hour'], ['year'], ['year', 'month'], ['DATE_UTC']]
GROUPING_NAMES_COLS = dict(zip(GROUPING_NAMES, GROUPING_COLS))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', default='plots')
    parser.add_argument('--case', choices=['building_lighting', 'demand_response', 'summer_load'])
    args = parser.parse_args()

    print('reading data')
    times = dict([('building_lighting', ['YearOnly', 'Month', 'MonthTOD']),
        ('demand_response', ['YearOnly', 'Month']), 
        ('summer_load', ['YearOnly', 'Month', 'MonthTOD', 'Hour'])])
    all_factors = get_all_factors(times[args.case])

    print('getting intervention effects')
    intervention_df, hours2017 = construct_intervention(args.case)
    intervention_effects_df = get_intervention_effects(intervention_df, hours2017, args.case, all_factors)
    
    print('plotting')
    plot_total_damages('EASIUR', intervention_effects_df, args.case, title=False)
    plot_total_damages('AP2', intervention_effects_df, args.case, title=False)
    for label in LABELS:
        get_stacked_plot(label, intervention_effects_df, args.case)


# Read in emissions factors
def get_all_factors(times):
    all_dfs = {}
    for kind in ['MEF', 'AEF']:
        for region in ['PJM', 'RFC']:
            for fuel_type in ['FossilOnly', 'FossilPlus']:
                for time in times:
                    if region == 'RFC' and fuel_type == 'FossilPlus': 
                        continue
                    if kind == 'MEF' and time == 'Hour':
                        continue
                    df = get_factor_df(kind=kind, time=time, region=region, fuel_type=fuel_type)
                    all_dfs[(kind, region, fuel_type, time)] = df
    return all_dfs

# Read in one emissions factor file
def get_factor_df(kind='MEF', time='MonthTOD', region='PJM', fuel_type='FossilOnly'):
    kind_folder = 'mefs' if kind=='MEF' else 'aefs'
    
    # Read in file
    if fuel_type == 'FossilOnly':
        region_breakdown = 'isorto' if region == 'PJM' else 'nerc'
        df = pd.read_csv(os.path.join(os.pardir, 'factor_estimates', 'calculated_factors', 
                                      kind_folder, time, 
                                      '{}_{}.csv'.format(region_breakdown, kind_folder)),
                         index_col=GROUPING_NAMES_COLS[time])
        df = df[df[region_breakdown] == region].drop(region_breakdown, axis=1)
    else:
        if region != 'PJM':
            raise NotImplementedError('fossil-plus factors are only available for PJM')
        df = pd.read_csv(os.path.join(os.pardir, 'factor_estimates', 'calculated_factors', 
                                      kind_folder, time, 
                                      'pjm_fplus_{}.csv'.format(kind_folder)),
                         index_col=GROUPING_NAMES_COLS[time])
        
    # Filter MEF columns
    if kind == 'MEF':
        df = df.drop([x for x in df.columns if '-r' in x or '-int' in x], axis=1)
        df.columns = [x.replace('-est', '') for x in df.columns]
        
    # Ensure columns have numeric type
    df = df.apply(pd.to_numeric, axis=1)
    
    return df


# Get intervention reduction (or addition) for every hour of the year
def construct_intervention(example_case):
    if example_case == 'building_lighting':
        HOURLY_REDUCTION_MWH = 100e-6
        NUM_HOURS_PER_DAY = 4
        hours2017 = pd.date_range('2017-01-01', '2018-01-01', freq='H', closed='left')
        intervention_df = \
            pd.DataFrame(data=hours2017.map(lambda x: HOURLY_REDUCTION_MWH if x.hour in [20,21,22,23] else 0),
                     index=hours2017, columns=['MWh'])
    elif example_case == 'demand_response':
        intervention_df = pd.DataFrame(pd.read_csv('monthly_dr.csv', index_col=0).stack())
        intervention_df.index.names = ['year', 'month']
        intervention_df.columns = ['MWh']

        # Run intervention in every month
        hours2017 = pd.date_range(start='2017-01-01', end='2017-12-31', freq='MS')
        intervention_df = intervention_df[intervention_df.index.get_level_values('year') == 2017]
        intervention_df.index = hours2017
    elif example_case == 'summer_load':
        metered_loads = pd.DataFrame(pd.read_csv(
            os.path.join(os.pardir, 'data', 'metered_loads', 'formatted_data', 'hourly_loads.csv'),
            index_col=0, parse_dates=[0]))['RTO-HrMeteredLoad']
        metered_loads = pd.DataFrame(metered_loads.loc['2017-01-01':'2017-12-31'])
        metered_loads.columns = ['MWh']

        # Measure load only in summer
        hours2017 = pd.date_range('2017-06-01', '2017-09-01', freq='H', closed='left')
        intervention_df = pd.DataFrame(metered_loads.loc[hours2017])

    return intervention_df, hours2017


# Get emissions and damages effect of intervention
def get_intervention_effects(intervention_df, hours2017, example_case, all_dfs):
    # Get factor for each point in time series
    hours2017_factors = {}
    for key in all_dfs.keys():
        df = all_dfs[key]
        
        get_time_factors = get_month_factors if example_case == 'demand_response' else get_hour_factors

        # 2017
        df2 = get_time_factors(df, key[-1], hours2017)
        hours2017_factors[key + (2017,)] = df2
        
        # 2016 for PJM fossil-plus
        if key[1] == 'PJM' and key[2] == 'FossilPlus' and key[-1] != 'Hour':
            df3 = get_time_factors(df, key[-1], hours2017, True)
            hours2017_factors[key + (2016,)] = df3


    # Calculate effects
    intervention_effects = {}
    for key in hours2017_factors.keys():
        reds = hours2017_factors[key].multiply(intervention_df['MWh'], axis='index')
        effects = reds[LABELS].sum()  # total effect
        
        # For MEFs, propagate error. 
        #   When same factor is applied to multiple reductions 
        #      (i.e. multiplied by their total reduction amount), this factor's SE should be summed across
        #      these reductions (i.e. also multiplied by the total reduction amount).
        #   Independent errors (from different factors) should then be combined by the sqrt of their
        #      sum of squares.
        if key[0] == 'MEF':
            
            # Per-factor (non-independent) errors
            groupby_list = dict([('YearOnly', reds.index.year), 
                                 ('Month', [reds.index.year, reds.index.month]),
                                 ('MonthTOD', [reds.index.year, reds.index.month, reds.index.hour]),
                                 ('Hour', [reds.index])])
            per_factor_errors = reds[['{}-se'.format(x) for x in LABELS]].groupby(
                groupby_list[key[-2]]).sum()
            
            # Combine per-factor errors to get independent errors
            ses = np.sqrt((per_factor_errors ** 2).sum())

            effects = pd.concat([effects, ses])
        intervention_effects[key] = effects

    intervention_effects_df = pd.DataFrame(intervention_effects).T
    intervention_effects_df.index.names = ['kind', 'region', 'fuel_type', 'time', 'year']

    return intervention_effects_df

# Helper function to get factors for point in time series
def get_hour_factors(df, time, hours, prev_year=False):
    year_series = hours.map(lambda x: x.year-1) if prev_year else hours.map(lambda x: x.year)
    month_series = hours.map(lambda x: x.month)
    hour_series = hours.map(lambda x: x.hour)
    every_hour_series = hours.map(lambda x: x.replace(year=x.year-1)) if prev_year else hours
    if time == 'YearOnly':
        df2 = df.loc[year_series]
    elif time == 'Month':
        df2 = df.loc[list(zip(year_series, month_series))]
    elif time == 'MonthTOD':
        df2 = df.loc[list(zip(year_series, month_series, hour_series))]
    elif time == 'Hour':
        df2 = df.loc[every_hour_series.map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))]
    df2 = df2.set_index(hours)
    return df2

def get_month_factors(df, time, months, prev_year=False):
    year_series = months.map(lambda x: x.year-1) if prev_year else months.map(lambda x: x.year)
    month_series = months.map(lambda x: x.month)
    if time == 'YearOnly':
        df2 = df.loc[year_series]
    elif time == 'Month':
        df2 = df.loc[list(zip(year_series, month_series))]
    df2 = df2.set_index(months)
    return df2

if __name__ == '__main__':
    main()
