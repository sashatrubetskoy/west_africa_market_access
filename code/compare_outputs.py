import argparse
import pandas as pd

parser = argparse.ArgumentParser() # Allows user to put no-borders in command line
parser.add_argument('--file_a', '-a', help='First output file to compare', type=str)
parser.add_argument('--file_b', '-b', help='Second output file to compare', type=str)
args = parser.parse_args()
UNIQUE = 'ORIG_FID'

df1 = pd.read_csv(args.file_a).set_index(UNIQUE)
df2 = pd.read_csv(args.file_b).set_index(UNIQUE)

df1['new ln MA'] = df2['ln MA']
df1['dif'] = df1['new ln MA'] - df1['ln MA']

outfile = 'output/compare_' + \
    args.file_a.split('/')[-1].split('.')[0] + '_' + args.file_b.split('/')[-1].split('.')[0] + '.csv'
df1.to_csv(outfile)