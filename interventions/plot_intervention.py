import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import os

dam_cols_ap2 = ['co2_dam', 'so2_dam_ap2', 'nox_dam_ap2', 'pm25_dam_ap2']
dam_cols_eas = ['co2_dam', 'so2_dam_eas', 'nox_dam_eas', 'pm25_dam_eas']

# Plotting total damage stacked plot
def plot_total_damages(dam_type, intervention_effects_df, example_case, title=False):
    
    fontsize=18
    
    plt.rcParams['hatch.linewidth'] = 0.5
    sns.set(style="whitegrid", color_codes=True)

    dam_cols = dam_cols_eas if dam_type == 'EASIUR' else dam_cols_ap2
    se_col = 'dam_{}-se'.format('eas' if dam_type == 'EASIUR' else 'ap2')

    df = get_onelabel_formatted(dam_cols, intervention_effects_df, example_case)
    if example_case == 'building_lighting':
        df = (df.set_index(['spat', 'kind', 'time'])).reset_index()
    elif example_case == 'demand_response':
        df = (df.set_index(['spat', 'kind', 'time'])/1e6).reset_index() # millions of dollars
    elif example_case == 'summer_load':
        df = (df.set_index(['spat', 'kind', 'time'])/1e9).reset_index() # billions of dollars
    
    df_cum = df.set_index(['spat', 'kind', 'time']).cumsum(axis=1).reset_index()

    # Stacked bar plot
    g = sns.FacetGrid(data=df_cum, col='spat', size=3, aspect=1)
    hatches = ['||', '///', '', '\\\\\\']


    hue_orders = dict([('building_lighting', ['Annual', 'Monthly', 'Monthly TOD']), 
        ('demand_response', ['Annual', 'Monthly']),
        ('summer_load', ['Annual', 'Monthly', 'Monthly TOD', 'Hourly'])])
    colors = dict([('building_lighting', [0,2,3]), ('demand_response', [0,2]), ('summer_load', [0,2,3,4])])
    g.map(sns.barplot, 'kind', dam_cols[-1], 'time', 
          hue_order=hue_orders[example_case], order=['Marginal', 'Average'],
          palette=[sns.color_palette('muted')[x] for x in colors[example_case]], edgecolor='black', hatch=hatches[0])  
    g.map(sns.barplot, 'kind', dam_cols[-2], 'time', 
          hue_order=hue_orders[example_case], order=['Marginal', 'Average'],
          palette=[sns.color_palette('muted')[x] for x in colors[example_case]], edgecolor='black', hatch=hatches[1])
    g.map(sns.barplot, 'kind', dam_cols[-3], 'time', 
          hue_order=hue_orders[example_case], order=['Marginal', 'Average'],
          palette=[sns.color_palette('muted')[x] for x in colors[example_case]], edgecolor='black', hatch=hatches[2])
    g.map(sns.barplot, 'kind', dam_cols[-4], 'time', 
          hue_order=hue_orders[example_case], order=['Marginal', 'Average'],
          palette=[sns.color_palette('muted')[x] for x in colors[example_case]], edgecolor='black', hatch=hatches[3]).set_titles('{col_name}')
    g.despine(left='true')

    # Legend, fontsize, and other formatting
    xoffset=0.035

    for i, ax in enumerate(g.axes.flatten()):

        ax.set_xlabel('') # No x-label

        if i == 0:
            # y label on left plot
            dollar_units = dict([('building_lighting', ''), ('demand_response', ' millions'), ('summer_load', ' billions')])
            ax.set_ylabel('Total damages\n{}(\${})'.format(
                '' if example_case == 'summer_load' else 'avoided ',
                dollar_units[example_case]))

            # pollutants legend
            leg_dict = dict(zip(dam_cols, ['CO$_2$', 'SO$_2$', 'NO$_x$', 'PM$_{{2.5}}$']))
            dam_patches = []
            for dam, hatch in zip(dam_cols, hatches[::-1]):
                patch = mpatches.Patch(facecolor='white', label=leg_dict[dam], edgecolor='black', hatch=hatch)
                dam_patches.append(patch)

            offsets = dict([('building_lighting', (0.16, -0.175)), ('demand_response', (0.18, -0.17)), ('summer_load', (0.16, -0.175))])
            lgd = ax.legend(handles=dam_patches, loc='center left', 
                            bbox_to_anchor=(0.3+xoffset, -0.15), ncol=4, frameon=True, fontsize=fontsize,
                            bbox_transform=plt.gcf().transFigure)
            plt.text(offsets[example_case][0]+xoffset, offsets[example_case][1], 'Pollutants:', transform=plt.gcf().transFigure,
                     fontsize=fontsize, fontweight='bold')
            lgd.get_frame().set_edgecolor('white')


        if i == 1:

            # temporal scope legend (same length as pollutants legend for alignment)
            if example_case == 'building_lighting':
                blank_patch = mpatches.Patch(color='white', label='')
                ann_patch = mpatches.Patch(color=sns.color_palette('muted')[0], label='Annual', edgecolor='black')
                month_patch = mpatches.Patch(color=sns.color_palette('muted')[2], label='Monthly', edgecolor='black')
                tod_patch = mpatches.Patch(color=sns.color_palette('muted')[3], label='Monthly TOD', edgecolor='black')
                time_patches = [blank_patch, ann_patch, month_patch, tod_patch, blank_patch]
                lgd2 = ax.legend(handles=time_patches, loc='center left', 
                                bbox_to_anchor=(0.19+xoffset, -0.025), ncol=5, frameon=True, fontsize=fontsize,
                                bbox_transform=plt.gcf().transFigure)
                plt.text(0.09+xoffset, -0.045, 'Temporal scopes:', transform=plt.gcf().transFigure, 
                         fontsize=fontsize, fontweight='bold')
            elif example_case == 'demand_response':
                blank_patch = mpatches.Patch(color='white', label='')
                ann_patch = mpatches.Patch(color=sns.color_palette('muted')[0], label='Annual', edgecolor='black')
                tod_patch = mpatches.Patch(color=sns.color_palette('muted')[2], label='Monthly', edgecolor='black')
                time_patches = [blank_patch, ann_patch, tod_patch, blank_patch]
                lgd2 = ax.legend(handles=time_patches, loc='center left', 
                                bbox_to_anchor=(0.3+xoffset, -0.0115), ncol=4, frameon=True, fontsize=fontsize,
                                bbox_transform=plt.gcf().transFigure)
                plt.text(0.11+xoffset, -0.0425, 'Temporal scopes:', transform=plt.gcf().transFigure, 
                         fontsize=fontsize, fontweight='bold')
            elif example_case == 'summer_load':
                blank_patch = mpatches.Patch(color='white', label='')
                ann_patch = mpatches.Patch(color=sns.color_palette('muted')[0], label='Annual', edgecolor='black')
                month_patch = mpatches.Patch(color=sns.color_palette('muted')[2], label='Monthly', edgecolor='black')
                tod_patch = mpatches.Patch(color=sns.color_palette('muted')[3], label='Monthly TOD', edgecolor='black')
                hr_patch = mpatches.Patch(color=sns.color_palette('muted')[4], label='Hourly', edgecolor='black')
                time_patches = [ann_patch, month_patch, tod_patch, hr_patch]
                lgd2 = ax.legend(handles=time_patches, loc='center left', 
                                bbox_to_anchor=(0.27+xoffset, -0.025), ncol=4, frameon=True, fontsize=fontsize-1,
                                bbox_transform=plt.gcf().transFigure)
                plt.text(0.09+xoffset, -0.045, 'Temporal scopes:', transform=plt.gcf().transFigure, 
                         fontsize=fontsize, fontweight='bold')

            lgd2.get_frame().set_edgecolor('white')
            
        # Annotate baseline
            # For building lighting: PJM fossil-plus marginal monthly TOD
            # For demand response: PJM fossil-plus marginal monthly
            # For summer load: PJM fossil-plus average monthly TOD
        baseline_locs = dict([('building_lighting', (2, 0.27)), 
            ('demand_response', (2, 0.2)), 
            ('summer_load', (2, 1.3))])
        if i == baseline_locs[example_case][0]:
            baseline_x = baseline_locs[example_case][1]
            patch_width = [p.get_width() for p in ax.patches][0]
            baseline_y = max([p.get_height() \
                          for p in ax.patches if abs(p.get_xy()[0]+patch_width/2-baseline_x)<=patch_width/4])
            ax.text(s='*', x=baseline_x, y=1.05 * baseline_y,
                   horizontalalignment='center', verticalalignment='center', 
                    fontsize=fontsize*2, fontweight='bold')
            
        # Set font size
        for item in ([
#             ax.title, 
            ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(fontsize)
        ax.title.set_fontsize(fontsize-2)


    # Hacky errorbars
    df_tot = get_onelabel_formatted(se_col[:-3], intervention_effects_df, example_case)
    df_tot_se = get_onelabel_formatted(se_col, intervention_effects_df, example_case)
    errbar_locs = dict([('building_lighting', [-0.27, 0, 0.27]), ('demand_response', [-0.2, 0.2]), ('summer_load', [-0.3,-0.1, 0.1])])
    for i, ax in enumerate(g.axes[0]):
        spat = df_tot['spat'].dtype.categories[i]
        df_tot_slice = df_tot.query('spat == @spat').query('kind == "Marginal"')
        df_tot_se_slice = df_tot_se.query('spat == @spat').query('kind == "Marginal"')

        if example_case == 'building_lighting':
            val, errval = df_tot_slice[se_col[:-3]].values, df_tot_se_slice[se_col].values
        elif example_case == 'demand_response':
            val, errval = df_tot_slice[se_col[:-3]].values/1e6, df_tot_se_slice[se_col].values/1e6
        elif example_case == 'summer_load':
            val, errval = df_tot_slice[se_col[:-3]].values/1e9, df_tot_se_slice[se_col].values/1e9

        ax.errorbar(errbar_locs[example_case], val, yerr=errval, ms=20, color='black', 
                        linewidth=0, elinewidth=2, capsize=2, capthick=2)   

    # Line around legend
    fig = plt.gcf()
    if example_case == 'building_lighting':
        leg_line = \
            mpatches.Rectangle(
                (0.073+xoffset, -0.2), 0.8, 0.24, facecolor='none', edgecolor='lightgray', 
                transform=fig.transFigure, figure=fig)
    elif example_case == 'demand_response':
        leg_line = \
            mpatches.Rectangle(
                (0.1+xoffset, -0.195), 0.77, 0.24, facecolor='none', edgecolor='lightgray', 
                transform=fig.transFigure, figure=fig)
    elif example_case == 'summer_load':
        leg_line = \
            mpatches.Rectangle(
                (0.073+xoffset, -0.2), 0.875, 0.24, facecolor='none', edgecolor='lightgray', 
                transform=fig.transFigure, figure=fig)
    fig.patches.extend([leg_line])

    extra_artists = (lgd, lgd2)
    if title:
        sup=fig.text(0.5, 0.9, 'Total damages ({})\n'.format(dam_type), 
                         fontsize=fontsize, fontweight='bold', fontstyle='italic',
                        transform=fig.transFigure, ha='center')
        extra_artists = extra_artists + (sup,)

    plt.tight_layout()
    dirname = os.path.join('plots', example_case)
    if not os.path.exists(dirname): os.makedirs(dirname)
    g.fig.savefig(os.path.join(dirname, 
                               '{}-stacked-with-error{}.pdf'.format(dam_type, '-titled' if title else '')),
                 bbox_extra_artists=extra_artists, bbox_inches='tight')


# Plotting one graph per damage factor
def get_stacked_plot(label, intervention_effects_df, example_case):
    df = get_onelabel_formatted(label, intervention_effects_df, example_case)
    df_se = get_onelabel_formatted('{}-se'.format(label), intervention_effects_df, example_case)
    
    # Get bar plot
    sns.set(style="whitegrid")
    colors = dict([('building_lighting', [0,2,3]), ('demand_response', [0,2]), ('summer_load', [0,2,3,4])])
    g = sns.catplot(x='kind', y=label, hue='time', col='spat', data=df,
                       kind='bar', palette=[sns.color_palette('muted')[x] for x in colors[example_case]], legend=False, ci=None,
                       height=3, aspect=1).set_titles('{col_name}')
    g.despine(left=True);
    
    # Adjust font size and add legend
    fontsize=18
    for i, ax in enumerate(g.axes.flatten()):
        ax.set_xlabel('')
        for item in ([#ax.title, 
                      ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(fontsize)
        ax.title.set_fontsize(fontsize-2)

        if i == 0:
            ncols = dict([('building_lighting', 3), ('demand_response', 2), ('summer_load', 4)])
            lgd = ax.legend(loc='center left', bbox_to_anchor=(0.75, -0.3), ncol=ncols[example_case], frameon=True, fontsize=fontsize)
            ax.set_ylabel(format_axis(label, example_case))
            
        # Annotate baseline
            # For building lighting: PJM fossil-plus marginal monthly TOD
            # For demand response: PJM fossil-plus marginal monthly
            # For summer load: PJM fossil-plus average monthly TOD
        baseline_locs = dict([('building_lighting', (2, 0.27)), ('demand_response', (2, 0.2)), ('summer_load', (2, 1.3))])
        if i == baseline_locs[example_case][0]:
            baseline_x = baseline_locs[example_case][1]
            patch_width = [p.get_width() for p in ax.patches][0]
            baseline_y = max([p.get_height() \
                          for p in ax.patches if abs(p.get_xy()[0]+patch_width/2-baseline_x)<=patch_width/4])
            ax.text(s='*', x=baseline_x, y=1.05 * baseline_y,
                   horizontalalignment='center', verticalalignment='center', 
                    fontsize=fontsize*2, fontweight='bold')
    
    # Hacky errorbars
    errbar_locs = dict([('building_lighting', [-0.27, 0, 0.27]), ('demand_response', [-0.2, 0.2]), ('summer_load', [-0.3,-0.1, 0.1])])
    for i, ax in enumerate(g.axes[0]):
        spat = df['spat'].dtype.categories[i]
        df_slice = df.query('spat == @spat').query('kind == "Marginal"')
        df_se_slice = df_se.query('spat == @spat').query('kind == "Marginal"')
        ax.errorbar(errbar_locs[example_case], df_slice[label].values,
                        yerr=df_se_slice['{}-se'.format(label)].values, ms=20, color='black', 
                        linewidth=0, elinewidth=2, capsize=2, capthick=2)
        
    # Plot title
    fig = plt.gcf()
#     sup=fig.text(0.5, 1, format_title(label), 
#              fontsize=fontsize, fontweight='bold', fontstyle='italic',
#             transform=fig.transFigure, ha='center')
    
    plt.tight_layout()
    
    dirname = os.path.join('plots', example_case)
    if not os.path.exists(dirname): os.makedirs(dirname)
    g.fig.savefig(os.path.join(dirname, 'si-{}.pdf'.format(label)),
                 bbox_extra_artists=(lgd,), #(lgd,sup), 
                  bbox_inches='tight')

## Formatting helpers

def get_dam_name(dam_abbr):
    return 'AP2' if dam_abbr == 'ap2' else 'EASIUR'
    
FULL_DAMS = ['dam_ap2', 'dam_eas']
def format_title(label):
    l = label.split('_')
    if label in FULL_DAMS:
        t = 'Total damages ({})'.format('AP2' if l[1] == 'ap2' else 'EASIUR')
    else:
        t = '{0}$_{{{1}}}$ {2}'.format(l[0][:2].upper(), l[0][2:], 'emissions' if l[1] == 'kg' else 'damages')
        if len(l) > 2: t += ' ({})'.format('AP2' if l[2] == 'ap2' else 'EASIUR')
    return t

def format_axis(label, example_case):
    l = label.split('_')
    if example_case == 'summer_load':
        if label in FULL_DAMS:
            t = 'Total damages ($)'
        elif len(l) > 2 or l[1] == 'dam':
            t = 'Damages ($)'
        else:
            t = 'Emissions (kg)'
    else:
        if label in FULL_DAMS:
            t = 'Total damages\navoided ($)'
        elif len(l) > 2 or l[1] == 'dam':
            t = 'Damages\navoided ($)'
        else:
            t = 'Emissions\navoided (kg)'
    
    return t

# Get formatted df with intervention effects for given label
def get_onelabel_formatted(label, intervention_effects_df, example_case):
    kind_map = dict([('MEF', 'Marginal'), ('AEF', 'Average')])
    time_map = dict([('YearOnly', 'Annual'), ('MonthTOD', 'Monthly TOD'), ('Month', 'Monthly'), ('Hour', 'Hourly')])
    
    df = intervention_effects_df[label].reset_index()
    df['spat'] = df.apply(
        lambda x: '{} ({}-{}{})'.format(
            x['region'], x['fuel_type'][:-4].lower(), x['fuel_type'][-4:].lower(), 
            ' 2016' if x['year'] == 2016 else ''), axis=1)
    df['spat'] = df['spat'].str.replace('fossil-plus', 'fossil+non-emit')
    df = df.drop(['region', 'fuel_type', 'year'], axis=1)
    df['kind'] = df['kind'].map(lambda x: kind_map[x]).astype(
        pd.CategoricalDtype(categories=['Marginal', 'Average'], ordered=True))

    times = dict([('building_lighting', ['Annual', 'Monthly', 'Monthly TOD']),
        ('demand_response', ['Annual', 'Monthly']),
        ('summer_load', ['Annual', 'Monthly', 'Monthly TOD', 'Hourly'])])
    df['time'] = df['time'].map(lambda x: time_map[x]).astype(
        pd.CategoricalDtype(categories=times[example_case], ordered=True))

    df['spat'] = df['spat'].astype(pd.CategoricalDtype(
        categories=['PJM (fossil-only)', 'PJM (fossil+non-emit 2016)', 'PJM (fossil+non-emit)', 'RFC (fossil-only)'], 
        ordered=True))
    df = df.sort_values(['spat', 'kind', 'time'])
    
    return df


