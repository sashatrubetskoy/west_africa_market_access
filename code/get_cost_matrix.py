# Alexandr (Sasha) Trubetskoy
# January 2019
# trub@uchicago.edu

import json
import time
import string
import random
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
parser.add_argument('--outfile', '-o', help='Set output location', type=str, default='data/csv/cost_matrix.csv')
args = parser.parse_args()

# 0. Make cost assumptions, set file names
#---------------------------------------------------
TCOST = pd.read_csv('parameters/transport_costs.csv').set_index('class').to_dict()['cost_per_km']
BCOST = pd.read_csv('parameters/border_costs.csv')
TARIFF = pd.read_csv('parameters/tariffs.csv').set_index('countrycode')
PARAMS = pd.read_csv('parameters/other_cost_parameters.csv').set_index('parameter').to_dict()['value']

CITIES_CSV = 'data/csv/cities.csv'
ROAD_FILE = 'data/geojson/roads.geojson'
# RAIL_FILE = # Rail not implemented yet
SEA_FILE = 'data/geojson/sea_links.geojson'
PORTS_FILE = 'data/geojson/ports.geojson'
BCROSS_FILE = 'data/geojson/border_crossings.geojson'
# EXTERNAL_TSV = None

logger.info('Cost matrix will export to {}.'.format(args.outfile))
#---------------------------------------------------


# 1. Read GeoJSONs
#---------------------------------------------------
def read_geojsons():

    def features_to_graph(features, z):
        # Directed graph is necessary because borders have
        # asymmetric costs
        G = nx.DiGraph() 
        for line in features:
            start = tuple(line['geometry']['coordinates'][0][0]+[z])
            end = tuple(line['geometry']['coordinates'][0][-1]+[z])
            
            # Add edge in both directions
            k = G.add_edge(start, end)
            k = G.add_edge(end, start)
            for prop in line['properties']:
                G[start][end][prop] = line['properties'][prop]
                G[end][start][prop] = line['properties'][prop]
        return G

    logger.info('1. Reading GeoJSONs...')

    # Roads need to be read in one country at a time.
    #  Create a separate graph for each country. Then
    #  connect the graphs at designated border points.
    with open(ROAD_FILE, 'r') as f:
        road_json = json.load(f)

    ## Get all the countries
    countries = set()
    for feature in road_json['features']:
        countries.add(feature['properties']['iso3'])

    ## Create & compose the graphs one at a time
    road = nx.DiGraph()
    for i, iso in enumerate(countries):
        road_features_i = [feature for feature in road_json['features'] if feature['properties']['iso3']==iso]
        G_i = features_to_graph(road_features_i, z=(100+i))
        road = nx.compose(road, G_i)
    
    ## Sea is separate. Rail is not implemented.
    # rail = geojson_to_graph(RAIL_FILE, z=1000)
    rail = nx.DiGraph() # Empty

    with open(SEA_FILE, 'r') as f:
        sea_json = json.load(f)
    sea = features_to_graph(sea_json['features'], z=500)

    G = nx.compose(road, rail)
    G = nx.compose(G, sea)
    logger.info('GeoJSONs read.')
    return road, rail, sea, G
#---------------------------------------------------


# 2. Find nearest nodes to cities
#---------------------------------------------------
def match_cities_with_nodes(road, rail, sea, G):
    cities = pd.read_csv(CITIES_CSV, converters={'nearest_road': eval, 'nearest_rail': eval, 'nearest_sea': eval, 'nearest_any': eval})
    road_nodes = np.array(list(road.nodes))
    rail_nodes = np.array(list(rail.nodes))
    sea_nodes = np.array(list(sea.nodes))
    any_nodes = np.array(list(G.nodes))

    # if ('nearest_road' not in cities.columns) or (args.force_rematch):
    logger.info('2. Matching cities with nodes...')
    def get_nearest_node(row):
        point = list(row[['X', 'Y']]) # X, Y coordinates of city in projection
        row['nearest_road'] = tuple(road_nodes[spatial.KDTree(road_nodes[:,:2]).query(point)[1]]) # scipy magic
        # row['nearest_rail'] = tuple(rail_nodes[spatial.KDTree(rail_nodes).query(point)[1]])
        row['nearest_sea'] = tuple(sea_nodes[spatial.KDTree(sea_nodes[:,:2]).query(point)[1]])
        row['nearest_any'] = tuple(any_nodes[spatial.KDTree(any_nodes[:,:2]).query(point)[1]])
        return row

    cities = cities.progress_apply(get_nearest_node, axis=1)
    cities.to_csv(CITIES_CSV, index=False)
    logger.info('\nCities matched.')
    # else:
    #     logger.info('2. Cities already matched.')
        
    return cities, road_nodes, rail_nodes, sea_nodes, any_nodes
#---------------------------------------------------


# 3. Add cost attributes to graph
#---------------------------------------------------
def add_costs_to_graph(G):
    logger.info('3. Adding costs to graph...')
    for u, v in G.edges:
        if 'cost' not in G[u][v]: # careful: costs are per km, length is in meters
            G[u][v]['cost'] = TCOST[str(G[u][v]['quality'])] * G[u][v]['length']/1000
    logger.info('Costs added.')
    return G
#---------------------------------------------------


# 4. Find nearest nodes to ports
#---------------------------------------------------
def find_nearest_nodes_to_ports(road_nodes, rail_nodes, sea_nodes, any_nodes):
    logger.info('4. Matching ports with nodes...')
    with open(PORTS_FILE, 'r') as p:
        ports_geojson = json.load(p)
    ports_nodes = [tuple(f['geometry']['coordinates']) for f in ports_geojson['features']]
    ports = pd.DataFrame(ports_nodes, columns=['X', 'Y'])

    def get_nearest_node(row):
        point = list(row[['X', 'Y']]) # X, Y coordinates of city in projection
        row['nearest_road'] = tuple(road_nodes[spatial.KDTree(road_nodes[:,:2]).query(point)[1]]) # scipy magic
        # row['nearest_rail'] = tuple(rail_nodes[spatial.KDTree(rail_nodes).query(point)[1]])
        row['nearest_sea'] = tuple(sea_nodes[spatial.KDTree(sea_nodes[:,:2]).query(point)[1]])
        row['nearest_any'] = tuple(any_nodes[spatial.KDTree(any_nodes[:,:2]).query(point)[1]])
        return row

    ports = ports.progress_apply(get_nearest_node, axis=1)
    logger.info('\nCities matched.')
    return ports
#---------------------------------------------------


# # X. Create road-to-rail transfers at cities within 10 km of rail
# #---------------------------------------------------
# def create_road_rail_transfers(cities, G):
#     logger.info('4. Creating road-rail transfers...')
#     for i in range(len(cities)):
#         x, y, u, v = list(cities.iloc[i][['X', 'Y', 'nearest_road', 'nearest_rail']])
#         if np.sqrt((x-v[0])**2 + (y-v[1])**2) < 10000:
#             G.add_edge(u, v,
#                 len_km=0,
#                 class_0='transfer',
#                 class_1='transfer', 
#                 cost_0=args.switching_fee,
#                 cost_1=args.switching_fee)
#     logger.info('Road-rail transfers matched.')
#     return G
# #---------------------------------------------------


# 5. Create road-to-sea transfers at ports
#---------------------------------------------------
def create_sea_transfers(ports, G):
    logger.info('5. Creating sea transfers...')
    for i in range(len(ports)):
        x, y, u, v = list(ports.iloc[i][['X', 'Y', 'nearest_road', 'nearest_sea']])
        port_is_near_road = np.sqrt((x-u[0])**2 + (y-u[1])**2) < 10000
        port_is_near_sea_link = np.sqrt((x-v[0])**2 + (y-v[1])**2) < 10000
        if port_is_near_road and port_is_near_sea_link:
            G.add_edge(u, v,
                length=0,
                quality='transfer',
                cost=PARAMS['port_fee'])
            G.add_edge(v, u,
                length=0,
                quality='transfer',
                cost=PARAMS['port_fee'])
    logger.info('Sea transfers created.')
    return G
#---------------------------------------------------


# 6. Create border crossings
#---------------------------------------------------
def create_border_crossings(road_nodes, G):
    logger.info('6. Creating border crossings...')
    with open(BCROSS_FILE, 'r') as f:
        border_crossings = json.load(f)

    for bc in border_crossings['features']:
        # Find which two nodes match the border crossing X,Y
        coords = bc['geometry']['coordinates']
        matches = [i for i, row in enumerate(road_nodes[:,:2]) if all(np.round(row, 8) == np.round(coords, 8))]
        if not matches:
            logger.info('\tThere is no road node at {}!'.format(coords))
            continue
        if len(matches) == 1: # This is typically at the edge of a region
            # logger.info('\tThere is only one road at {}!'.format(coords))
            continue
        a, b = [tuple(road_nodes[i]) for i in matches]

        # Find which countries the two nodes are in
        country_a, country_b = [G[n][list(G[n])[0]]['iso3'] for n in [a, b]]

        # If cost is manually specified in the GeoJSON,
        # use that cost. Otherwise default to BCOST csv.
        cost_a = bc['properties']['border_cost'] if bc['properties']['border_cost'] != -1 else BCOST.loc[country_a][country_b]
        cost_b = bc['properties']['border_cost'] if bc['properties']['border_cost'] != -1 else BCOST.loc[country_b][country_a]

        G.add_edge(a, b,
            length=0,
            quality='border_crossing',
            cost=cost_a)
        G.add_edge(b, a,
            length=0,
            quality='border_crossing',
            cost=cost_b)
    logger.info('Border crossings created.')
    return G
#---------------------------------------------------


# 7. Run cost matrix calculation
#---------------------------------------------------
def get_cost_matrix(cities, G):
    all_cities = cities['ORIG_FID'].tolist() # Field just needs to be a unique ID
    country_of = cities.set_index('nearest_any').to_dict()['iso3']
    nearest_node = cities.set_index('ORIG_FID').to_dict()['nearest_any']
    
    matrix_dict = dict()

    counter = 0
    n_iter = len(all_cities)
    t_0 = time.time()
    for city_a in all_cities:
        counter += 1
        print('{:.2f}% done.   Elapsed: {:.1f}m    Time remain: {:.1f}m    Avg {:.2f} s/iter...'.format(
            100*counter/n_iter, 
            (time.time()- t_0)/60, 
            (n_iter-counter)*(time.time()- t_0)/(60 * counter), 
            (time.time()- t_0)/counter),
            end='\r')

        city_a_node = nearest_node[city_a]
        city_a_node = (city_a_node[0], city_a_node[1], int(city_a_node[2]))
        costs, paths = nx.single_source_dijkstra(G, city_a_node, weight='cost')
        costs_cities = []

        for city_b in all_cities:
            if city_a == city_b:
                costs_cities.append(0.0)
                continue

            city_b_node = nearest_node[city_b]
            
            # (Raw transport cost + border costs) / shipment value [ad valorem]
            transport_cost = costs[city_b_node] / PARAMS['shipment_value']
            # Tariffs at destination [ad valorem]
            tariff = TARIFF.loc[country_of[city_b_node]]['tariff']

            if country_of[city_a_node] == country_of[city_b_node]:
                final_cost = transport_cost
            else:
                final_cost = transport_cost + tariff

            costs_cities.append(final_cost)

        matrix_dict[city_a] = costs_cities

    print('\r100% done.   Elapsed: {:.1f}m    Time remain: {:.1f}m    Avg {:.2f} s/iter...'.format(
        (time.time()- t_0)/60,
        (n_iter-counter)*(time.time()- t_0)/(60 * counter), 
        (time.time()- t_0)/counter))

    matrix = pd.DataFrame.from_dict(matrix_dict, orient='index')
    matrix.columns = all_cities
    return matrix
#---------------------------------------------------


# Wrapper functions
#---------------------------------------------------
def setup():
    road, rail, sea, G = read_geojsons()
    cities, road_nodes, rail_nodes, sea_nodes, any_nodes = match_cities_with_nodes(road, rail, sea, G)
    G = add_costs_to_graph(G)
    # G = create_road_rail_transfers(cities, G)
    ports = find_nearest_nodes_to_ports(road_nodes, rail_nodes, sea_nodes, any_nodes)
    G = create_sea_transfers(ports, G)
    G = create_border_crossings(road_nodes, G)
    # G, externals = set_up_external_markets(ports, G)
    return road, rail, sea, G, cities


def main(road, rail, sea, G, cities):    
    logger.info('# of nodes: {}, # of edges: {}'.format(G.number_of_nodes(), G.number_of_edges()))
    

    logger.info('7. Calculating cost matrices...')
    cost_matrix = get_cost_matrix(cities, G)

    cost_matrix.to_csv(args.outfile)

    logger.info('All done.')
    return cost_matrix
#---------------------------------------------------

road, rail, sea, G, cities = setup()
cost_matrix = main(road, rail, sea, G, cities)