import argparse
import os
import pandas as pd
import numpy as np
from scipy.stats import linregress as lm

import ipdb
import sys
from IPython.core import ultratb
sys.excepthook = ultratb.FormattedTB(mode='Verbose',
     color_scheme='Linux', call_pdb=1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', default='calculated_factors')
    parser.add_argument('--factorType', choices=['average', 'marginal'], required=True,
        help='type of factor to compute')
    parser.add_argument('--endYear', type=int, default=2017)
    args = parser.parse_args()

    # Read and process data
    print('getting data')
    rto_df, nerc_df, pjm_fplus_df = read_process_data(args.factorType, args.endYear)

    # # Calculate factors and save results
    print('calculating factors')
    save = args.save
    calc_factors = calculate_mefs if args.factorType == 'marginal' else calculate_aefs
    grouping_names = ['SeasonalTOD', 'MonthTOD', 'TOD', 'YearOnly', 'Month']
    grouping_cols = [['year', 'season', 'hour'], ['year', 'month', 'hour'], 
        ['year', 'hour'], ['year'], ['year', 'month']]

    for grouping_name, grouping in zip(grouping_names, grouping_cols):
        print('{}:'.format(grouping_name))
        print('PJM fossil-plus...')
        calc_factors(pjm_fplus_df, 'pjm_fplus', grouping, grouping_name, save)
        print('ISO/RTO...')
        calc_factors(rto_df, 'isorto', grouping + ['isorto'], grouping_name, save)
        print('NERC...')
        calc_factors(nerc_df, 'nerc', grouping + ['nerc'], grouping_name, save)

    if args.factorType == 'average':
        grouping = ['DATE_UTC']
        print('Hour:')
        print('PJM fossil-plus...')
        calculate_aefs_hourly(pjm_fplus_df, 'pjm_fplus', grouping, save)
        print('ISO/RTO...')
        calculate_aefs_hourly(rto_df, 'isorto', grouping + ['isorto'], save)
        print('NERC...')
        calculate_aefs_hourly(nerc_df, 'nerc', grouping + ['nerc'], save)


# Global variables for regression labels and x-column name
LABELS = ['so2_kg', 'nox_kg', 'pm25_kg', 'co2_kg',
    'so2_dam_ap2', 'nox_dam_ap2', 'pm25_dam_ap2', 
    'so2_dam_eas', 'nox_dam_eas', 'pm25_dam_eas',
    'co2_dam']
XCOL = 'gload_mwh'

# Global variables for AP2 vs. EASIUR columns
DAM_COLS_AP2 = ['co2_dam', 'so2_dam_ap2', 'nox_dam_ap2', 'pm25_dam_ap2']
DAM_COLS_EAS = ['co2_dam', 'so2_dam_eas', 'nox_dam_eas', 'pm25_dam_eas']

def read_process_data(factor_type, end_year):
    filename_add = '' if factor_type == 'average' else '_diffs'

    # Generation, emissions, and damages aggregated by ISO/RTO
    rto_df = pd.read_csv(
        os.path.join(os.pardir, 'data', 'cems', 'formatted_data', 
            'cems{}_isorto.csv'.format(filename_add)), 
        index_col=0, parse_dates=[0])
    rto_df = rto_df[rto_df.index.year <= end_year]

    # Generation, emissions, and damages aggregated by NERC region
    nerc_df = pd.read_csv(
        os.path.join(os.pardir, 'data', 'cems', 'formatted_data', 
            'cems{}_nerc.csv'.format(filename_add)), 
        index_col=0, parse_dates=[0])
    nerc_df = nerc_df[nerc_df.index.year <= end_year]

    # PJM generation by fuel type.
    #   Note: Non-emitting categories are: Hydro, Nuclear, Solar, Wind, Other Renewables
    pjm_by_fuel = pd.read_csv(
        os.path.join(os.pardir, 'data', 'pjm_gen_by_fuel', 'formatted_data', 
            'pjm_gen_by_fuel_type_wide.csv'),
        index_col=0, parse_dates=[0])

    # PJM non-emitting generation
    NON_EMIT = ['Uranium', 'Wind', 'Hydro', 'Solar', 'Other Renewables']
    NON_EMIT2 = ['Nuclear', 'Wind', 'Hydro', 'Solar', 'Other Renewables']
    if factor_type == 'marginal':
        # Indicator variables for whether fuel type is marginal (only used for marginal factors)
        #    Note: Wind, Solar, and Nuclear (Uranium) are represented in marginal data.
        #      Hydro, and Other Renewables (or naming variants) are never marginal.
        selector = pd.read_csv(
            os.path.join(os.pardir, 'data', 'pjm_marginal_fuel', 'formatted_data', 
                'marginal_fuels.csv'), index_col=0, parse_dates=[0])
        selector = selector.reindex(columns=NON_EMIT)
        selector.columns = [x.replace('Uranium', 'Nuclear') for x in selector.columns]
        selector = selector.fillna(0).applymap(lambda x: 1 if x > 0 else 0)
        selector.index = selector.index.tz_localize(None)   # ensure naive datetime index

        # Difference, and then select differences in marginal hours only
        pjm_non_emitting = (pjm_by_fuel.diff() * selector)[NON_EMIT2].dropna(how='all')
        pjm_non_emitting = pd.DataFrame(pjm_non_emitting.sum(axis=1))
    else:
        # Get total non-emitting generation in each hour
        pjm_non_emitting = pd.DataFrame(pjm_by_fuel[NON_EMIT2].sum(axis=1)).dropna(how='all')
    pjm_non_emitting.columns = [XCOL]

    # Construct data frame with PJM fossil-plus generation
    pjm_fplus_df = pd.DataFrame(rto_df[rto_df['isorto'] == 'PJM'])
    pjm_fplus_df = pjm_fplus_df.drop('isorto', axis=1)
    pjm_fplus_df[XCOL] = pjm_fplus_df[XCOL] + pjm_non_emitting[XCOL]
    pjm_fplus_df = pjm_fplus_df[pjm_fplus_df.index.year <= end_year].dropna()

    # Label temporal groupings
    rto_df = label_temporal_groupings(rto_df)
    nerc_df = label_temporal_groupings(nerc_df)
    pjm_fplus_df = label_temporal_groupings(pjm_fplus_df)

    return rto_df, nerc_df, pjm_fplus_df

def label_temporal_groupings(df):
    # Copy df to not change in place
    df = df.copy()

    # Get year, month, hour
    df['year'] = df.index.year
    df['month'] = df.index.month
    df['hour'] = df.index.hour

    # Get season
    #  Summer = May-Sept
    #  Winter = Dec-Mar
    #  Transition = Apr, Oct
    month_to_season = ['winter'] * 3 + ['trans'] + ['summer'] * 5 + ['trans'] + ['winter'] * 2
    df['season'] = df.index.map(lambda x: month_to_season[x.month - 1])

    return df


def calculate_mefs(df, df_name, grouping, grouping_name, save):

    def calc_mefs_helper(data):
        x = data[XCOL].values
        y = data[LABELS]
        # Run regression for each column and store results
        results = y.apply(lambda v: lm(x,v))
        return results

    # Get regression results
    results_df = factor_calculation_helper(df, grouping, calc_mefs_helper)
    results_df = format_regression_results(results_df)
    results_df = sum_damages(results_df, 'MEF')
    
    # Save factors
    dirname = os.path.join(save, 'mefs', grouping_name)
    if not os.path.exists(dirname): os.makedirs(dirname)
    results_df.to_csv(os.path.join(dirname, '{}_mefs.csv'.format(df_name)))


def calculate_aefs(df, df_name, grouping, grouping_name, save):

    def calc_aefs_helper(data):
        sums = data[[XCOL]+LABELS].dropna().sum()
        results = sums[LABELS] / sums[XCOL]

        return results

    # Get calculated AEFs
    results_df = factor_calculation_helper(df, grouping, calc_aefs_helper)
    results_df = sum_damages(results_df, 'AEF')
    
    # Save factors
    dirname = os.path.join(save, 'aefs', grouping_name)
    if not os.path.exists(dirname): os.makedirs(dirname)
    results_df.to_csv(os.path.join(dirname, '{}_aefs.csv'.format(df_name)))

def calculate_aefs_hourly(df, df_name, grouping, save):

    # Divide emissions/damages by generation, preserving index information 
    df = df.reset_index().set_index(grouping)
    # results_df = df[LABELS] / df[XCOL]
    results_df = df[LABELS].apply(lambda x: x / df[XCOL])
    results_df = sum_damages(results_df, 'AEF')

    # Save factors
    dirname = os.path.join(save, 'aefs', 'Hour')
    if not os.path.exists(dirname): os.makedirs(dirname)
    results_df.to_csv(os.path.join(dirname, '{}_aefs.csv'.format(df_name)))


def factor_calculation_helper(df, grouping, calc_fn):
    df = df.dropna()
    groups = df.groupby(grouping)

    # Calculate factor within each group
    results_dict = {}
    for name, data in groups:
        results_dict[name] = calc_fn(data)

    # Format results into one data frame
    results_df = pd.DataFrame.from_dict(results_dict, orient='index')
    results_df.index.names = grouping
    return results_df


def format_regression_results(results_df):
    # Extract slopes, standard error, r-value, and intercept
    stats_list = []
    stats_fns = [lambda x: x.slope, lambda x: x.stderr, lambda x: x.rvalue, lambda x: x.intercept]
    stats_labels = ['est', 'se', 'r', 'int']
    for fn, label in zip(stats_fns, stats_labels):
        df = results_df.applymap(fn).add_suffix('-{}'.format(label))
        stats_list.append(df)

    # Concatenate extracted values and sort columns in order
    sep_results_df = pd.concat(stats_list, axis=1)
    col_order = np.array(
        ['{0}-est,{0}-se,{0}-r,{0}-int'.format(x).split(',') for x in LABELS]).flatten()
    return sep_results_df.reindex(col_order, axis=1)


def sum_damages(df, factor_type):
    # For each of AP2 and EASIUR, get total damage factor and add to df
    for cols, col_type in zip([DAM_COLS_AP2, DAM_COLS_EAS], ['ap2', 'eas']):
        df = sum_damages_helper(df, cols, col_type, factor_type)
    return df

def sum_damages_helper(df, dam_cols, dam_type, factor_type):
    # For MEFs, total factor is sum of ests, and SE is sqrt of sum of squares of SEs
    #   For AEFs, simply sum ests to get total factor
    if factor_type == 'MEF':
        total_dam_est = df[['{}-est'.format(x) for x in dam_cols]].sum(axis=1)
        total_dam_se = np.sqrt((df[['{}-se'.format(x) for x in dam_cols]] ** 2).sum(axis=1))
        total_dam_cols = pd.concat([total_dam_est, total_dam_se], axis=1)
        total_dam_cols.columns = ['dam_{}-est'.format(dam_type), 'dam_{}-se'.format(dam_type)]
    else:
        total_dam_cols = pd.DataFrame(df[dam_cols].sum(axis=1))
        total_dam_cols.columns = ['dam_{}'.format(dam_type)]
    df = pd.concat([df, total_dam_cols], axis=1)
    return df


if __name__=='__main__':
    main()