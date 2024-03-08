"""

TrackUpstream.py

Version: 1.3

Date: 25 May 2021

Description
===========


For each element 'i' of the drainage network, the program tracks all the
upstream elements draining to the element i. Based on the area of each
catchment, provided in the input file, the program calculates the surface
of the draining area.


The program reads in an ASCII file, comma-delimited, containing topological
information about the drainage network. This information consists of the start
and end nodes of each element of the network. Normally, this file is the same
used in when running the program connectivity.py.

The information must be organized in tabular form, with each row containing the
information for one element of the drainage network, and  the columns are
comma-separated elements.
The first row is a header, with the names of the columns. The columns that must
be present in the file are:

1. System ID
2. 'from' node
3. 'to' node
4. Area of the catchment (units must be taken into account by the user)
5. Flow extracted at the catchment

The program stores the follwing information:

1. A Python list containing a new list for each element 'i' of the drainage
   network. Each of these sub-lists contains the IDs of all the elements
   draining to the element 'i'. The information is stored in the a binary file
   drainnetwork_sid.bin.
   
2. Same information as above, but the elements are identified by an index that
   corresponds to the order in which the elements were read in from the text
   file provided. The information is stored in the a binary file
   drainnetwork_fid.bin.
   
3. A Python list where each element is the surface of the draining area.
   The information is stored in the file drainage_area.bin.

Date: 25 May 2021

Code modified to be compatible with Python 3.

"""

import numpy
import string
import sys
import pickle
import os
import argparse
from progress.bar import Bar


parser = argparse.ArgumentParser(description="", add_help=True)
parser.add_argument('input_file', help='Text file organized as CSV (comma-separated) containing the following information:\\n1. RCH_ID of the drainage element\n2. Integer: number of the start node\n3. Integer: number of the end node\n4. Area of the catchment (m**2)\n5. Flow being extracted at the basin.\n\n')


# read input arguments
args = parser.parse_args()
inputfile = args.input_file

# open the file containing the micro-basins covering the
# region of study
fregion = open(inputfile, 'r')
contents_microbasins = fregion.readlines()
numlines = len(contents_microbasins)
numelements = numlines-1

idsistecol = numpy.zeros(numelements, dtype=numpy.int32)
fromnode = numpy.zeros(numelements, dtype=numpy.int32)
tonode = numpy.zeros(numelements, dtype=numpy.int32)
microarea = numpy.zeros(numelements, dtype=numpy.float32)

# the toelement vector does not refers to the system id, but to normal
# indices of the system's vector
toelement = numpy.zeros(numelements, dtype=numpy.int32)
toelement[:] = -1

for i in range(numlines-1):
  #splitted = string.split(contents_microbasins[i+1], sep=",")
  splitted = contents_microbasins[i+1].split(sep=",")
  idsistecol[i] = int(splitted[0])
  fromnode[i] = int(splitted[1])
  tonode[i] = int(splitted[2])
  microarea[i] = float(splitted[3])



# Check if the previous files exist
# That would keep us from recalculating if something goes wrong with the area
print("=========================================")
print("       Calculating drainage network")
print("=========================================")
if os.path.isfile('drainnetwork_sid.bin'):
        print()
        print("ATTENTION: File 'drainnetwork_.bin' already exists.")
        print("This file contains information about the drainage area")
        print("associated to each catchment.")
        print()
        answer = input("Do you want to overwrite this file (yes/no)? ")
        if answer.upper() == 'NO':
                print("\n\nFinished")
                sys.exit(0)
        else:
          # remove the previous file
          os.remove('drainnetwork_sid.bin')



if not os.path.isfile('drainnetwork_sid.bin'):
  # we have to load the information about the connectivity
  if not os.path.isfile('connectivity.bin'):
    print()
    print("ATTENTION: File 'connectivity.bin' not found.")
    print("Finished.")
    print()
    sys.exit(1)


  fconnec = open('connectivity.bin', 'rb')
  connectivity = pickle.load(fconnec)
  fconnec.close()

  drainnetwork_fid = []  # store an index
  drainnetwork_sid = []  # store the RCH_ID

  # We have to go calculate the drainage area of each
  # catchment

  # LM 2019-06-06
  # Calculate 10% of the data

  bar = Bar("Processing", max = len(idsistecol))
  for j in range(len(idsistecol)):
    # Let's keep track of what is happening
    #print "%6i%10i%6i/%6i" % (j,idsistecol[j],j+1,len(idsistecol))
    basinseq_fid = []
    basinseq_sid = []
  
    for k in range(len(connectivity)):
      result = (idsistecol[j] in connectivity[k])
      if result == True:
        basinseq_sid.append(connectivity[k][0])
        basinseq_fid.append(k)

    # Every element of the list, corresponds to one basin.
    # All the sub-elements of that list (basin) drain all to that basin
    # HOWEVER the elements of the basin are not ordered, i.e., the last
    # element downstream is not the first of the network
    drainnetwork_fid.append(basinseq_fid)
    drainnetwork_sid.append(basinseq_sid)
    bar.next()

  # for debuggin purposes, let's store the information in a binary file
  fout_sid = open('drainnetwork_sid.bin', 'wb')
  pickle.dump(drainnetwork_sid, fout_sid, pickle.HIGHEST_PROTOCOL)
  fout_sid.close()

  fout_fid = open('drainnetwork_fid.bin', 'wb')
  pickle.dump(drainnetwork_fid, fout_fid, pickle.HIGHEST_PROTOCOL)
  fout_fid.close()
  bar.finish()
else:
  fin_sid = open('drainnetwork_sid.bin', 'rb')
  drainnetwork_sid = pickle.load(fin_sid)
  fin_sid.close()
  fin_fid =  open('drainnetwork_fid.bin', 'rb')
  drainnetwork_fid = pickle.load(fin_fid)
  fin_fid.close()
  

#=============================================================================
# At this point, we should also calculate area of each basin
#

print("=========================================")
print("           Quantifying surface")
print("=========================================")


BasinArea = numpy.zeros(numelements, dtype=numpy.float32)
for j in range(len(idsistecol)):
  accumArea = 0.
  OneNetwork = drainnetwork_sid[j]
  for micro_sid in OneNetwork:
    tup1 = numpy.where(micro_sid == idsistecol)
    if len(tup1[0]) == 0:
      continue
    elif len(tup1[0]) > 1:
      print("\nThere is an error at this point\n")
      print("RCHID = %i" % (idsistecol[j]))
      sys.exit(1)
    accumArea += microarea[tup1[0]]
  BasinArea[j] = accumArea

  
# for debuggin purposes, let's store the information in a binary file
fout_area = open('drainage_area.bin','wb')
pickle.dump(BasinArea, fout_area, pickle.HIGHEST_PROTOCOL)
fout_area.close()
