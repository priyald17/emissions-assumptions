import os
import pandas as pd
import numpy as np

from datetime import datetime
import calendar

import matplotlib.pyplot as plt
from matplotlib import gridspec

def main():

    # Read in data
    print('reading in data')
    all_dfs = {}
    for kind in ['MEF', 'AEF']:
        for region in ['PJM', 'RFC']:
            for fuel_type in ['FossilOnly', 'FossilPlus']:
                for time in ['YearOnly', 'Month', 'MonthTOD']:
                    if region == 'RFC' and fuel_type == 'FossilPlus': 
                        continue
                    df = get_factor_df(kind=kind, time=time, region=region, fuel_type=fuel_type)
                    all_dfs[(kind, region, fuel_type, time)] = df

    # Get annual/monthly plots
    print('creating annual/monthly plots')
    for label in ['co2_kg', 'co2_dam',
                  'so2_kg', 'so2_dam_ap2', 'so2_dam_eas',
                  'nox_kg', 'nox_dam_ap2', 'nox_dam_eas',
                  'pm25_kg', 'pm25_dam_ap2', 'pm25_dam_eas',
                  'dam_ap2', 'dam_eas']:
        plot_over_time_annual(label, all_dfs)
        plot_over_time_monthly(label, all_dfs)
        plot_over_time_annual_monthly(label, all_dfs)

    # Get month TOD main plots
    print('creating truncated month TOD plots')
    month_tod_paper_plot('co2_kg', all_dfs, (0,900));
    month_tod_paper_plot('so2_kg', all_dfs, (0,3));
    month_tod_paper_plot('dam_ap2', all_dfs, (0,150));

    # Get month TOD SI plots
    print('creating full month TOD plots')
    ylims_dict = dict([
        ['co2_kg', (0,900)], ['so2_kg', (0,3)], ['nox_kg', (0,1.3)], ['pm25_kg', (0,0.15)],
        ['co2_dam', (0,40)], ['so2_dam_eas', (0,100)], ['so2_dam_ap2', (0,120)],
        ['nox_dam_eas', (0,15)], ['nox_dam_ap2', (0,7)], 
        ['pm25_dam_eas', (0,15)], ['pm25_dam_ap2', (0,20)],
        ['dam_eas', (0,150)], ['dam_ap2', (0,150)]
    ])
    for label, ylim in ylims_dict.items():
        month_tod_si_plot(label, all_dfs, ylim)


# Global variables describing temporal groupings and their associated columns
GROUPING_NAMES = ['SeasonalTOD', 'MonthTOD', 'TOD', 'YearOnly', 'Month']
GROUPING_COLS = [['year', 'season', 'hour'], ['year', 'month', 'hour'], 
        ['year', 'hour'], ['year'], ['year', 'month']]
GROUPING_NAMES_COLS = dict(zip(GROUPING_NAMES, GROUPING_COLS))


def get_factor_df(kind='MEF', time='MonthTOD', region='PJM', fuel_type='FossilOnly'):
    kind_folder = 'mefs' if kind=='MEF' else 'aefs'
    
    # Read in file
    if fuel_type == 'FossilOnly':
        region_breakdown = 'isorto' if region == 'PJM' else 'nerc'
        df = pd.read_csv(os.path.join('calculated_factors', kind_folder, time, 
                                      '{}_{}.csv'.format(region_breakdown, kind_folder)),
                         index_col=GROUPING_NAMES_COLS[time])
        df = df[df[region_breakdown] == region].drop(region_breakdown, axis=1)
    else:
        if region != 'PJM':
            raise NotImplementedError('fossil-plus factors are only available for PJM')
        df = pd.read_csv(os.path.join('calculated_factors', kind_folder, time, 
                                      'pjm_fplus_{}.csv'.format(kind_folder)),
                         index_col=GROUPING_NAMES_COLS[time])
        
    # Filter MEF columns
    if kind == 'MEF':
        df = df.drop([x for x in df.columns if '-r' in x or '-int' in x], axis=1)
        df.columns = [x.replace('-est', '') for x in df.columns]
        
    # Ensure columns have numeric type
    df = df.apply(pd.to_numeric, axis=1)
    
    return df

def plot_over_time_annual(label, all_dfs):
    fig, ax = plt.subplots(figsize=(8.5, 4))
    lgd = plot_over_time_helper(label, all_dfs, ax, time='YearOnly')
    
    dirname = os.path.join('plots', 'annual_monthly')
    if not os.path.exists(dirname): os.makedirs(dirname)
    fig.savefig(os.path.join(dirname, '{}-annualOnly.pdf'.format(label)), 
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()
    
def plot_over_time_monthly(label, all_dfs):
    fig, ax = plt.subplots(figsize=(8.5, 4))
    lgd = plot_over_time_helper(label, all_dfs, ax, time='Month')
    
    dirname = os.path.join('plots', 'annual_monthly')
    if not os.path.exists(dirname): os.makedirs(dirname)
    fig.savefig(os.path.join(dirname, '{}-monthlyOnly.pdf'.format(label)), 
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()
    
def plot_over_time_annual_monthly(label, all_dfs):
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 7))
    lgd = plot_over_time_helper(label, all_dfs, axes[0], time='YearOnly', lgd_y=-0.03)
    plot_over_time_helper(label, all_dfs, axes[1], time='Month', legend=False)

    # Ensure plots have same y axis limits
    max_y = max([ax.get_ylim()[1] for ax in axes])
    for ax in axes:
        ax.set_ylim(0, max_y)

    plt.tight_layout()
    
    dirname = os.path.join('plots', 'annual_monthly')
    if not os.path.exists(dirname): os.makedirs(dirname)
    fig.savefig(os.path.join(dirname, '{}-annualMonthly.pdf'.format(label)), 
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()

def plot_over_time_helper(label, df_dict, ax, time='YearOnly', legend=True, lgd_y=-0.09):    
    
    # Set x ticks
    xticks = pd.date_range(start='2006-01-01', end='2018-01-05', freq='AS')[:-1]
    xticks = xticks[::2]
        
    # Factors to plot and style attributes for each
    kinds = [('PJM', 'FossilOnly'), ('RFC', 'FossilOnly'), ('PJM', 'FossilPlus')]
    mstyles = ['s', '.', '^']
    msizes = [4,8,4] if time == 'YearOnly' else [3,6,3]
    colors = ['blue', 'green', 'red']
    lw = 2 if time == 'YearOnly' else 1

    for kind, mstyle, msize, color in zip(kinds, mstyles, msizes, colors):
        leglab = '{} ({}-{})'.format(kind[0], kind[1][:-4].lower(), kind[1][-4:].lower())
        leglab = leglab.replace('fossil-plus', 'fossil+non-emitting')

        # Plot marginal factors
        marg = format_idx(df_dict[('MEF',) + kind + (time,)], time)
        marg[label].plot(ax=ax, yerr=marg['{}-se'.format(label)], 
                         marker=mstyle, markersize=msize,
                         legend=False, label='{} (MEF)'.format(leglab),
                         ls='-', mew=1, color=color, xticks=xticks.to_pydatetime(), 
                         lw=lw)

        # Plot average factors
        avg = format_idx(df_dict[('AEF',) + kind + (time,)], time)      
        avg[label].plot(ax=ax, marker=mstyle, markersize=msize, mew=1,
                        legend=False, label='{} (AEF)'.format(leglab),
                        ls='--', color=color, markerfacecolor='white', 
                        xticks=xticks.to_pydatetime(), lw=lw)
            
    # Format x- and y-axis label
    ylabel = 'Damage factor (\$/MWh)' if 'dam' in label else 'Emissions factor\n(kg/MWh)'
    ax.set_ylabel(ylabel)
    ax.set_xlabel('Year' if time == 'YearOnly' else 'Month/Year') 

    # Set x limits, x tick label format, and y limits
    ax.set_xlim('2006-01-01', '2018-01-05')
    ax.set_xticklabels([x.strftime('\'%y') for x in xticks])
    ax.set_ylim(0,)

    # Font size
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(14)

    # Legend
    if legend:
        lgd_handles, lgd_labels = ax.get_legend_handles_labels()
        order = [3,0,4,1,5,2]   # hard-coded label order
        lgd = ax.legend([lgd_handles[idx] for idx in order],[lgd_labels[idx] for idx in order],
                  loc='center', bbox_to_anchor=(0.5, lgd_y), ncol=3, fontsize=12.5,
                    columnspacing=0.8, bbox_transform=plt.gcf().transFigure)
        return lgd
    else:
        return None

def month_tod_paper_plot(label, df_dict, ylim, year=2017):
    figsize=(12,4)
    outer_dims=(2,1)
    inner_dims=(1,3)
    months_to_plot=[5,11]
    lgd_ncol=1
    lgd_bbox_to_anchor=(1.05, 1.6)
    use_suptitle=False
    hspace=0.5
    subtitle_break=' '
    filename_add = 'main'
    month_tod_plot_helper(label, df_dict, ylim, year, 
        figsize, outer_dims, inner_dims, months_to_plot,
        hspace, subtitle_break,
        lgd_ncol, lgd_bbox_to_anchor, use_suptitle,
        filename_add)

def month_tod_si_plot(label, df_dict, ylim, year=2017):
    figsize=(22,16)
    outer_dims=(6,2)
    inner_dims=(1,6)
    months_to_plot=range(1,13)
    lgd_ncol = 2
    lgd_bbox_to_anchor=(-3.35, -0.35)
    use_suptitle=False
    hspace=0.4
    subtitle_break='\n'
    filename_add = 'si'
    month_tod_plot_helper(label, df_dict, ylim, year, 
        figsize, outer_dims, inner_dims, months_to_plot,
        hspace, subtitle_break, 
        lgd_ncol, lgd_bbox_to_anchor, use_suptitle,
        filename_add)

def month_tod_plot_helper(label, df_dict, ylim, year,
                     figsize, outer_dims, inner_dims, months_to_plot,
                     hspace, subtitle_break,
                     lgd_ncol, lgd_bbox_to_anchor, use_suptitle,
                     filename_add):
    fontsize=16
    fig = plt.figure(figsize=figsize)
    outer = gridspec.GridSpec(*outer_dims, wspace=-0.45, hspace=hspace)
    
    def get_month_only(df, month, year):
        df = df.reset_index().query('month=={}'.format(month)).query('year=={}'.format(year))
        df = df.drop(['year', 'month'], axis=1).set_index('hour')
        return df
    
    for i, month in enumerate(months_to_plot):
        inner = gridspec.GridSpecFromSubplotSpec(*inner_dims, 
            subplot_spec=outer[i], wspace=0.1, hspace=0.1)
        for j, kind in enumerate(
            [('PJM', 'FossilPlus'), ('PJM', 'FossilOnly'), ('RFC', 'FossilOnly')]):
            ax = plt.Subplot(fig, inner[j])
            fig.add_subplot(ax)
            ncol = outer_dims[1]
            
            # Plot average factors for this month
            avg = get_month_only(df_dict[('AEF',) + kind + ('MonthTOD',)], month, year)    
            avg[label].plot(ax=ax, marker='*', legend=False, label='Average',
                                  ls='--', markersize=5.5, color='green')
            
            # Plot marginal factors for this month
            marg = get_month_only(df_dict[('MEF',) + kind + ('MonthTOD',)], month, year)
            marg[label].plot(ax=ax, marker='o', legend=False, label='Marginal',
                        ls='-', markersize=3, color='blue',
                        yerr=marg['{}-se'.format(label)])
            
            # Set y limits
            ax.set_ylim(*ylim)
            
            # Add titles to plots (for both month and region/gen mix)
            #   For plots at top, indicate which region/gen mix
            if month in months_to_plot[:ncol]:
                title_formatted = '{}{}({}-{})\n\n'.format(
                    kind[0], subtitle_break, kind[1][:-4].lower(), kind[1][-4:].lower())
                title_formatted = title_formatted.replace('fossil-plus', 
                    'fossil+non-emitting' if filename_add=='main' else 'fossil+non-emit')
                ax.set_title(title_formatted, 
                    fontweight='bold')
            #  For plots in the middle, indicate which month (and deal with cases where
            #   we've already used the title attribute for region/gen mix labels)
            if j == 1:
                if month in months_to_plot[:ncol]:
                    ax.text(0.5,1.09, calendar.month_abbr[month],
                            horizontalalignment='center', verticalalignment='center', 
                            transform=ax.transAxes, fontsize=fontsize)
                else:
                    ax.set_title(calendar.month_abbr[month])
        
            # Add x-axis label to middle plots at bottom
            if month in months_to_plot[-ncol:] and j == 1:
                ax.set_xlabel('Hour of day (UTC-5)')
            else:
                ax.set_xlabel('')
        
            # Add y-axis label on left column only, and y-axis ticks on left plots within each month
            if (i % ncol) == 0 and j == 0:
                ylabel = \
                'Damage factor\n(\$/MWh)' if 'dam' in label else 'Emissions factor\n(kg/MWh)'
                ax.set_ylabel(ylabel)
            if j > 0:
                ax.set_yticklabels([])
            
            # Set larger font size
            for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                         ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

            # Add legend at bottom (to last plot)
            if i == len(months_to_plot)-1 and j == 2:
                lgd = ax.legend(ncol=lgd_ncol, bbox_to_anchor=lgd_bbox_to_anchor, 
                                      loc='upper left', fontsize=fontsize)
                
    # Overall title for plot 
    if use_suptitle:
        sup = plt.suptitle('{} ({})'.format(format_title(label), year),  x=0.375, y=0.97,
                           fontsize=fontsize, fontweight='bold', fontstyle='italic')
        extra_artists = (lgd,sup)
    else:
        extra_artists = (lgd,)
    
    dirname = os.path.join('plots', 'month_tod')
    if not os.path.exists(dirname): os.makedirs(dirname)
    fig.savefig(os.path.join(dirname,'{}-{}.pdf'.format(filename_add, label)), 
                bbox_extra_artists=extra_artists, bbox_inches='tight')
    plt.close()


def format_idx(df, time):
    df_dt = df.copy()
    if time == 'Month':
        df_dt.index = df_dt.index.map(lambda x: datetime(x[0], x[1], 1))
    else:
        df_dt.index = df_dt.index.map(lambda x: datetime(x, 1, 1))
    return df_dt

FULL_DAMS = ['dam_ap2', 'dam_eas']
def format_title(label):
    l = label.split('_')
    if label in FULL_DAMS:
        t = 'Total damages ({})'.format('AP2' if l[1] == 'ap2' else 'EASIUR')
    else:
        t = '{0}$_{{{1}}}$ {2}'.format(
            l[0][:2].upper(), l[0][2:], 'emissions' if l[1] == 'kg' else 'damages')
        if len(l) > 2: t += ' ({})'.format('AP2' if l[2] == 'ap2' else 'EASIUR')
    return t



if __name__=='__main__':
    main()