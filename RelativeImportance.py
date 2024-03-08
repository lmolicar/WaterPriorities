"""

RelativeImportance.py

Version: 1.3

Date: 25 May 2021

Description
===========


Calculates the priority of each catchment in a drainage network.
The relative importance of catchment 'i' is calculated as the
surface of the catchment 'i' times the sum the ratio between
the flux extracted at each catchment 'j' downstream of 'i' and the
corresponding draining surface associated to 'j'.

Reads in the following information:

1. Drainage network associated with each catchment.
   This information is contained in the file

   drainnetwork_sid.bin
   drainnetwork_fid.bin

2. Draining area associated with each catchment.
   Information contained in the file

   drainage_area.bin

3. Catchment information. Normally, it is the input file used in the previous
   steps. The information must be organized in tabular form, with each row
   containing the information for one element of the drainage network, and
   the columns are comma-separated elements. The first row is a header, with
   the names of the columns. The columns that must be present in the file are:

   1. System ID
   2. 'from' node
   3. 'to' node
   4. Area of the catchment (units must be taken into account by the user)
   5. Flow extracted at the catchment


Date: 06 June 2019

The script was modified to work with input areas other than the actual area
of the micro-catchment, like when establishing priorities for conservation,
where it is the area of forest that is important to establish priorities.

Date: 25 May 2021

Code modified to be compatible with Python 3.

"""

import pickle
import numpy as np
import string
import sys
import argparse
from progress.bar import Bar

parser = argparse.ArgumentParser(description="", add_help=True)
parser.add_argument('input_file', help='Text file organized as CSV (comma-separated) containing the following information:\\n1. RCH_ID of the drainage element\n2. Integer: number of the start node\n3. Integer: number of the end node\n4. Area of the catchment (m**2)\n5. Flow being extracted at the basin.\n\n')


# read input arguments
args = parser.parse_args()
fname_region = args.input_file

fname_area = "drainage_area.bin"
fname_connect = "connectivity_Recno.bin"

# Read in catchment information
fextract = open(fname_region, 'r')
contents = fextract.readlines()
numlines = len(contents)
numcatchments = numlines-1  # skip the header
fextract.close()
arrID = np.zeros(numcatchments, dtype=np.int32)
arrFlow =  np.zeros(numcatchments, dtype=np.float32)
arrCatchArea = np.zeros(numcatchments, dtype=np.float32)
arrRI = np.zeros(numcatchments, dtype=np.float32)
for i in range(1,numlines):  # skip the header
  #splitted = string.split(string.strip(contents[i]), sep=',')
  splitted = contents[i].strip().split(sep = ",")
  arrID[i-1] = int(splitted[0])
  arrCatchArea[i-1] = np.float32(splitted[3])
  arrFlow[i-1] = np.float32(splitted[4])
        

# Load the file with the surface of the basin
farea = open(fname_area, 'rb')
list_area = pickle.load(farea)
drainArea = np.array(list_area)
farea.close()

# Load the connectivity of each element of the network
# Each element of the list is associated in the same order
# to Rch_id. Each element is a list of Rch_ids downstream

fconnect = open(fname_connect,'rb')
connectRecno = pickle.load(fconnect)
fconnect.close()



#=============================================================================
# Calculate the relative importance of each catchment

bar = Bar("Processing", max = numcatchments)
for i in range(numcatchments):
  catchmentRI = 0.
  for downIndex in connectRecno[i]:

    # LM 06-June-2019
    if drainArea[downIndex] < 1e-36:
      catchmentRI = 0.
    else:
      catchmentRI += arrFlow[downIndex] *  arrCatchArea[i] / drainArea[downIndex]

  arrRI[i] = catchmentRI
  bar.next()


bar.finish()


# Write out the priority associated to each catchment in text, comma-separated
# file, to link then to the shape of the catchments
fname_priority_text = "Priority.txt"
fpriority_text = open(fname_priority_text, 'w')
out_contents = []
header = "RCHID,RI\n"
out_contents.append(header)
for i in range(numcatchments):
  oneLine = "%i,%f\n" % (arrID[i],arrRI[i])
  out_contents.append(oneLine)

fpriority_text.writelines(out_contents)
fpriority_text.close()

