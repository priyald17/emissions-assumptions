import argparse
import os
import pandas as pd
from datetime import timedelta

'''
    Get formatted PJM hourly metered loads.
    Input: Hourly metered load data, downloaded from PJM DataMiner2 (for RTO region).
        Link: https://dataminer2.pjm.com/feed/hrl_load_metered/definition
        (Note: Old data is from 
            https://pjm.com/markets-and-operations/ops-analysis/historical-load-data.aspx)
    Output: Clean hourly metered load data.
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', default='formatted_data', 
        help='save folder path')
    args = parser.parse_args()

    # Read in and format load data
    print('getting load data')
    df = pd.read_csv(os.path.join('raw_data', 'hrl_load_metered.csv'),
        parse_dates=['datetime_beginning_utc'], index_col='datetime_beginning_utc',
        usecols=['datetime_beginning_utc', 'mw'])
    df.index = df.index + timedelta(hours=-5)  # TODO: currently dates are actually UTC-5
    df.index.names =['DATE_UTC']
    df.columns = ['RTO-HrMeteredLoad'] # TODO: add units (MW)

    # Save data
    print('saving data')
    save = args.save
    if not os.path.exists(save): os.makedirs(save)
    df.to_csv(os.path.join(save, 'hourly_loads.csv'))


if __name__=='__main__':
    main()