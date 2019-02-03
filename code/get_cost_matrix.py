# Alexandr (Sasha) Trubetskoy
# January 2019
# trub@uchicago.edu

import argparse
import itertools
import json
import logging
import pickle
import random
import string
import time
import numpy as np
import pandas as pd
import networkx as nx
from collections import OrderedDict
from scipy import spatial, special
from tqdm import tqdm, tqdm_pandas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tqdm.pandas() # Gives us nice progress bars
parser = argparse.ArgumentParser() # Allows user to put no-borders in command line
parser.add_argument('--outfile', '-o', help='Set output location', type=str, default='data/csv/cost_matrix.csv')
parser.add_argument('--bcross_file', '-b', help='Give border crossing GeoJSON location', type=str, default='data/geojson/border_crossings.geojson')
parser.add_argument('--time', '-t', help='Use time instead of freight cost', action='store_true')
args = parser.parse_args()

# 0. Make cost assumptions, set file names
#---------------------------------------------------
TCOST = pd.read_csv('parameters/transport_costs.csv').set_index('class').to_dict()['cost_per_km']
if args.time:
    TCOST = pd.read_csv('parameters/transport_speeds.csv').set_index('class')
    TCOST['cost_per_km'] = 1 / TCOST['km_per_hour'] # Convert to hours per km
    TCOST = TCOST.to_dict()['cost_per_km']
BCOST = pd.read_csv('parameters/border_costs.csv', index_col=0)
TARIFF = pd.read_csv('parameters/tariffs.csv').set_index('countrycode')
PARAMS = pd.read_csv('parameters/other_cost_parameters.csv').set_index('parameter').to_dict()['value']

CITIES_CSV = 'data/csv/cities.csv'
ROAD_FILE = 'data/geojson/roads.geojson'
# RAIL_FILE = # Rail not implemented yet
SEA_FILE = 'data/geojson/sea_links.geojson'
PORTS_FILE = 'data/geojson/ports.geojson'
BCROSS_FILE = args.bcross_file
# EXTERNAL_TSV = None

logger.info('Cost matrix will export to {}.'.format(args.outfile))
#---------------------------------------------------


# 1. Read GeoJSONs
#---------------------------------------------------
def read_geojsons():

    def features_to_graph(features, iso):
        # Directed graph is necessary because borders have
        # asymmetric costs
        G = nx.DiGraph() 
        for line in features:
            start = tuple(line['geometry']['coordinates'][0][0]+[iso])
            end = tuple(line['geometry']['coordinates'][0][-1]+[iso])

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
    for iso in countries:
        road_features_i = [feature for feature in road_json['features'] if feature['properties']['iso3']==iso]
        G_i = features_to_graph(road_features_i, iso)
        road = nx.compose(road, G_i)
    
    ## Sea is separate. Rail is not implemented.
    # rail = geojson_to_graph(RAIL_FILE, z=1000)
    rail = nx.DiGraph() # Empty

    with open(SEA_FILE, 'r') as f:
        sea_json = json.load(f)
    sea = features_to_graph(sea_json['features'], 'sea')

    G = nx.compose(road, rail)
    G = nx.compose(G, sea)
    logger.info('GeoJSONs read.')
    return road, rail, sea, G
#---------------------------------------------------


# 2. Find nearest nodes to cities
#---------------------------------------------------
def get_highest_quality_node_within_radius(point, iso3, nodelist, g, r=0.05):
    nodes_just_xy = np.array([(node[0], node[1]) for node in nodelist], dtype=np.float64) # Ignore country
    kdtree_query_result_node_ids = spatial.KDTree(nodes_just_xy).query(point, k=500, distance_upper_bound=r)[1] # Use scipy magic to quickly get nearest nodes. Get 0.1 degrees = ~10 km
    all_within_r_ids = list(OrderedDict.fromkeys(kdtree_query_result_node_ids)) # Remove duplicates preserving order
    all_within_r_ids = [a for a in all_within_r_ids if a != len(nodelist)] # Since the result is padded with placeholder value if fewer than k are found
    all_within_r = [tuple(nodelist[i]) for i in all_within_r_ids] # Get actual nodes
    
    # Make sure nodes are within the city's country
    all_within_r = [node for node in all_within_r if node[2]==iso3]

    # If there are no nodes within radius, just take the closest node
    if not all_within_r:
        idx = spatial.KDTree(nodes_just_xy).query(point)[1]
        return tuple(nodelist[idx])

    # Find highest quality level within radius
    def max_quality(node):
        best_q_dest = sorted(g[node], key=lambda x: g[node][x]['quality'])[-1]
        return g[node][best_q_dest]['quality']

    best_quality = 0
    for candidate in all_within_r:
        candidate_max_quality = max_quality(candidate)
        if candidate_max_quality > best_quality:
            best_quality = candidate_max_quality

    # Find closest node of that quality
    return next(node for node in all_within_r if max_quality(node)==best_quality)


def match_cities_with_nodes(road, rail, sea, G):
    cities = pd.read_csv(CITIES_CSV, converters={'nearest_road': eval, 'nearest_rail': eval, 'nearest_sea': eval, 'nearest_any': eval})
    road_nodes = list(road.nodes)
    rail_nodes = list(rail.nodes)
    sea_nodes = list(sea.nodes)
    any_nodes = list(G.nodes)

    # if ('nearest_road' not in cities.columns) or (args.force_rematch):
    logger.info('2. Matching cities with nodes...')
    def get_nearest_node(row):
        point = list(row[['X', 'Y']]) # X, Y coordinates of city in projection
        iso3 = row['iso3']
        row['nearest_road'] = get_highest_quality_node_within_radius(point, iso3, road_nodes, road)
        # row['nearest_rail'] = get_highest_quality_node_within_radius(point, rail_nodes, rail)
        row['nearest_sea'] = tuple(sea_nodes[spatial.KDTree(np.array([(n[0], n[1]) for n in sea_nodes], dtype=np.float64)).query(point)[1]])
        # row['nearest_any'] = sorted([row['nearest_road'], row['nearest_sea']],
        #     key=lambda x: np.linalg.norm(np.array(point) - np.array(x[:2]))\
        #     )[0]
        row['nearest_any'] = row['nearest_road']
        return row
    cities = cities.progress_apply(get_nearest_node, axis=1)
    cities.to_csv(CITIES_CSV, index=False)
    logger.info('\nCities matched.')
        
    return cities, road_nodes, rail_nodes, sea_nodes, any_nodes
#---------------------------------------------------


# 3. Add cost attributes to graph
#---------------------------------------------------
def add_costs_to_graph(G):
    logger.info('3. Adding costs to graph...')
    for u, v in G.edges:
        if 'cost' not in G[u][v]: # careful: costs are per km, length is in meters
            G[u][v]['cost'] = TCOST[str(G[u][v]['quality'])] * G[u][v]['length']/1000
            G[v][u]['cost'] = TCOST[str(G[v][u]['quality'])] * G[v][u]['length']/1000
    logger.info('Costs added.')
    return G
#---------------------------------------------------


# 4. Find nearest nodes to ports
#---------------------------------------------------
def find_nearest_nodes_to_ports(road, rail, sea, G):
    with open(PORTS_FILE, 'r') as p:
        ports_geojson = json.load(p)
    ports_nodes = [tuple(f['geometry']['coordinates']) for f in ports_geojson['features']]
    ports = pd.DataFrame(ports_nodes, columns=['X', 'Y'])
    road_nodes = list(road.nodes)
    rail_nodes = list(rail.nodes)
    sea_nodes = list(sea.nodes)
    any_nodes = list(G.nodes)
    
    logger.info('4. Matching ports with nodes...')
    def get_nearest_node(row):
        point = list(row[['X', 'Y']]) # X, Y coordinates of city in projection
        row['nearest_road'] = get_highest_quality_node_within_radius(point, 'sea', road_nodes, road)
        # row['nearest_rail'] = get_highest_quality_node_within_radius(point, rail_nodes, rail)
        row['nearest_sea'] = tuple(sea_nodes[spatial.KDTree(np.array([(n[0], n[1]) for n in sea_nodes], dtype=np.float64)).query(point)[1]])
        row['nearest_any'] = sorted([row['nearest_road'], row['nearest_sea']],
            key=lambda x: np.linalg.norm(np.array(point) - np.array(x[:2]))\
            )[0]
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
#         if np.sqrt((x-v[0])**2 + (y-v[1])**2) < 0.1:
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
        port_is_near_road = np.sqrt((x-u[0])**2 + (y-u[1])**2) < 0.05
        port_is_near_sea_link = np.sqrt((x-v[0])**2 + (y-v[1])**2) < 0.05
        if port_is_near_road and port_is_near_sea_link:
            G.add_edge(u, v,
                length=0,
                quality='port_fee',
                cost=PARAMS['port_wait_time'] if args.time else PARAMS['port_fee'])
            G.add_edge(v, u,
                length=0,
                quality='port_fee',
                cost=PARAMS['port_wait_time'] if args.time else PARAMS['port_fee'])
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
        assert bc['geometry']['type'] == 'Point', 'Border crossings are {}. They must have type Point!'.format(bc['geometry']['type'])

        # Find which two nodes match the border crossing X,Y
        coords = bc['geometry']['coordinates']
        matches = [i for i, row in enumerate(np.array([(n[0], n[1]) for n in road_nodes], dtype=np.float64)) if all(np.round(row, 6) == np.round(coords, 6))]
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
        if args.time:
            cost_a = bc['properties']['border_cost'] if bc['properties']['border_cost'] != -1 else PARAMS['default_border_wait_time']
            cost_b = bc['properties']['border_cost'] if bc['properties']['border_cost'] != -1 else PARAMS['default_border_wait_time']
        else:
            cost_a = bc['properties']['border_cost'] if bc['properties']['border_cost'] != -1 else BCOST.loc[country_a][country_b]
            cost_b = bc['properties']['border_cost'] if bc['properties']['border_cost'] != -1 else BCOST.loc[country_b][country_a]
            
        if min([cost_a, cost_b]) < 0:
            logger.warning('Border cost is less than zero!')

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
        costs, paths = nx.single_source_dijkstra(G, city_a_node, weight='cost')
        costs_cities = []

        for city_b in all_cities:
            if city_a == city_b:
                costs_cities.append(0.0)
                continue

            city_b_node = nearest_node[city_b]
            
            if args.time:
                transport_cost = costs[city_b_node]
                tariff = 0 # No tariffs if using time
            else:
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
    ports = find_nearest_nodes_to_ports(road, rail, sea, G)
    G = create_sea_transfers(ports, G)
    G = create_border_crossings(road_nodes, G)
    pickle.dump([(e, G[e[0]][e[1]]['cost'], G[e[1]][e[0]]['cost']) for e in G.edges], open('test', 'wb'))
    # G, externals = set_up_external_markets(ports, G)
    # with open('edges.txt', 'w') as f:
    #     f.writelines([str(e)+'\n' for e in list(G.edges)])
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