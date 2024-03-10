import argparse
from water_priorities_utils import *


parser = argparse.ArgumentParser(description="Setting priorities for water conservation", add_help=True)
parser.add_argument('input_file', help='Text file organized as CSV (comma-separated) containing the following information:\\n1. RCH_ID of the drainage element\n2. Integer: number of the start node\n3. Integer: number of the end node\n4. Area of the catchment (m**2)\n5. Flow being extracted at the basin.\n\n')


# read input arguments
args = parser.parse_args()
inputfile = args.input_file

df, conectividad, conectividadRecno = Connectivity(inputfile)
BasinArea = TrackUpstream(df, conectividad)
RelativeImportance(df, BasinArea, conectividadRecno)