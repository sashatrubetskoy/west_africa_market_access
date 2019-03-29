# Alexandr (Sasha) Trubetskoy
# January 2019
# trub@uchicago.edu

import time
import logging
import argparse
import itertools
import numpy as np
import pandas as pd
import networkx as nx
from scipy import spatial, special
from tqdm import tqdm, tqdm_pandas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tqdm.pandas() # Gives us nice progress bars
parser = argparse.ArgumentParser() # Allows user to put no-borders in command line
parser.add_argument('--infile', '-i', help='Set location of input cost matrix', type=str, default='data/csv/cost_matrix.csv')
parser.add_argument('--outfile', '-o', help='Set output location', type=str, default='output/market_access.csv')
parser.add_argument('--harris', '-harris', help='Calculate MA for Harris 1954-style market potential (theta=1)', action='store_true')
args = parser.parse_args()

# 0. Make assumptions, set file names
#---------------------------------------------------
PARAMS = pd.read_csv('parameters/market_access_parameters.csv').set_index('parameter').to_dict()['value']
if args.harris:
    PARAMS['theta'] = 1
CITIES_CSV = 'data/csv/cities.csv'
UNIQUE_FIELD = 'ORIG_FID'
logger.info('File will export to {}.'.format(args.outfile))
#---------------------------------------------------


# 1. Read cost matrices
#---------------------------------------------------
def read_cost_matrix():
    logger.info('Reading cost matrix...')
    matrix = pd.read_csv(args.infile, index_col=0)
    matrix.index = matrix.index.astype(str) # Just in case...
    # Minimum cost, to prevent crazy values for cities that happen to be very close to each other
    matrix = matrix.clip(lower=PARAMS['min_cost'])
    return matrix
#---------------------------------------------------


# 2. Read cities and external markets
#---------------------------------------------------
def read_cities_and_externals():
    logger.info('Reading cities...')
    cities = pd.read_csv(CITIES_CSV)
    externals = {}
    return cities, externals
#---------------------------------------------------


# 3. Run MA
#---------------------------------------------------
def calc_market_access(city_i, cost_matrix, cities, externals):
    FMA, CMA = 0, 0

    # First get external market terms
    if externals:
        for ext in externals:
            travel_cost_id = cost_matrix.loc[city_i][ext] # Cost to export from i -> d
            travel_cost_oi = cost_matrix.loc[ext][city_i] # Cost to import from o -> i

            FMA = (1/travel_cost_id)**theta * externals[ext]['GDP'] # Firm Market Access
            CMA = (1/travel_cost_oi)**theta * externals[ext]['GDP'] # Consumer Market Access

    # Then add terms for all other cities as in Donaldson & Hornbeck 2016
    t0 = time.time()
    for i in range(len(cities)):
        logger.debug(city_i, i, cities.iloc[i][UNIQUE_FIELD])
        logger.debug(time.time())
        
        other_city = str(cities.iloc[i][UNIQUE_FIELD])
        if other_city == city_i:
            continue

        else:
            travel_cost_id = cost_matrix.loc[other_city][city_i]
            travel_cost_oi = cost_matrix.loc[city_i][other_city]

            if travel_cost_id < 0: # Skip city pairs where cost is set to -1, a dummy value
                continue

        if args.harris:
            logger.debug('        ', time.time())
            FMA += cities.iloc[i]['GDP'] / travel_cost_id # Firm Market Access
            logger.debug('FMA done', time.time())
            CMA += cities.iloc[i]['GDP'] / travel_cost_oi # Consumer Market Access
            logger.debug('CMA done', time.time())
        else:
            logger.debug('        ', time.time())
            FMA += cities.iloc[i]['GDP'] * (travel_cost_id + 1)**(-PARAMS['theta']) # Firm Market Access
            logger.debug('FMA done', time.time())
            CMA += cities.iloc[i]['GDP'] * (travel_cost_oi + 1)**(-PARAMS['theta']) # Consumer Market Access
            logger.debug('CMA done', time.time())

    return max([FMA, 1e-99]), max([CMA, 1e-99]) # in case MA = 0, prevent division errors later

def add_ma_cols(row, matrix, cities, externals):
    current_city_id = str(row[UNIQUE_FIELD])
    FMA, CMA = calc_market_access(current_city_id, matrix, cities, externals)
    row['ln MA'] = (1-PARAMS['beta'])*np.log(FMA) + PARAMS['beta']*np.log(CMA) # Initial overall market access
    
    return row

#---------------------------------------------------

matrix = read_cost_matrix()
cities, externals = read_cities_and_externals()

logger.info('3. Calculating market access...')
cities = cities.progress_apply(add_ma_cols, axis=1, args=(matrix, cities, externals))    
logger.info('\nMarket access calculated.')

logger.info('4. Exporting to {}...'.format(args.outfile))
cities.to_csv(args.outfile, index=False)
logger.info('All done.')