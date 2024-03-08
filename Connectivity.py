"""

Connectivity.py

Version: 1.3

Date: 25 May 2021

Description
===========


For each element of a drainage network, the program finds the list of elements
downstream.

The program reads in an ASCII file, comma-delimited, containing topological
information about the drainage network. This information consists of the start
and end nodes of each element of the network.
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

1. A Python list where each element corresponds to a list of the elements
   downstream of a given catchment. The elements are identified by their ID.
   The information is stored in the as a cPickle element in the file
   connectivity.bin.

2. A Python list where each element corresponds to a list of the elements
   downstream of a given catchment. In this case, the elements are identified
   by and index. The index is consistent with the order in which the elements
   were read in from the input file. The information is stored in the as a
   cPickle element in the file connectivity_Recno.bin.
   
Final elements are those where the 'to element' field
is equal to -1.

Date: 25 May 2021

Code modified to be compatible with Python 3.

"""
import pickle
import numpy
import string
import sys
import os
import argparse
from progress.bar import Bar


parser = argparse.ArgumentParser(description="", add_help=True)
parser.add_argument('input_file', help='Text file organized as CSV (comma-separated) containing the following information:\\n1. RCH_ID of the drainage element\n2. Integer: number of the start node\n3. Integer: number of the end node\n4. Area of the catchment (m**2)\n5. Flow being extracted at the basin.\n\n')


# read input arguments
args = parser.parse_args()
inputfile = args.input_file
fin = open(inputfile, 'r')

# we make a first check now to overwrite existing files
if os.path.isfile('connectivity.bin'):
  print()
  print("ATTENTION: File 'connectivity.bin' already exists.")
  print("This file contains information about the connectivity")
  print("of each element of the drainage network.")
  print()
  answer = input("Do you want to overwrite this file (yes/no)? ")
  if answer.upper() == 'NO':
    print("\n\nFinished")
    sys.exit(0)


# read the contents. A text file is expected
contents = fin.readlines()
fin.close()

# It is better to store ID and nodes information in separate vectors
# Determine the number of lines to create the approprate vectors
# (substract the line of the header)
numlines = len(contents)
numelements = numlines-1

idsistecol = numpy.zeros(numelements, dtype=numpy.int32)
fromnode = numpy.zeros(numelements, dtype=numpy.int32)
tonode = numpy.zeros(numelements, dtype=numpy.int32)

# the toelement vector does not refers to the system id, but to normal
# indices of the system's vector
toelement = numpy.zeros(numelements, dtype=numpy.int32)
toelement[:] = -1

for i in range(numlines-1):
  #splitted = string.split(contents[i+1], sep=",")  # skip the header
  splitted = contents[i+1].split(",")
  idsistecol[i] = int(splitted[0])
  fromnode[i] = int(splitted[1])
  tonode[i] = int(splitted[2])


# for each element of the network, determine the next element
# downstream
for j in range(numelements):
  tupindex = numpy.where(fromnode == tonode[j])
  index = tupindex[0]
  if len(index) > 0:
    # however, if there are more than to elements, it means that
    # there is a problem with the network
    if len(index) > 1:
      print("RCH_ID = ",idsistecol[j])
      print("There is a problem with the network.")
      print("Two or more elements share the same starting node.")
      print("Aborted.")
      sys.exit(1)

    # otherwise, we are fine
    toelement[j] = index[0]
    continue


# Now let's calculate the connectivity.
# For each element of the network, we will trace every element
# downstream to the final element.
bigbuffer = []
bigbufferRecno = []

bar = Bar("Processing", max = numelements)
for k1 in range(numelements):
  # lists are not very efficient, but are practical :-)
  buffer = []
  bufferRecno = []
  buffer.append(idsistecol[k1])
  bufferRecno.append(k1)
  k2 = k1
  while(True):
    k2 = toelement[k2]
    if k2 > 0:
      buffer.append(idsistecol[k2])
      bufferRecno.append(k2)
      continue
    else:
      break
      
  bigbuffer.append(buffer)
  bigbufferRecno.append(bufferRecno)
  bar.next()

bar.finish()

# for now, let's store the connectivity in a file for debugging purposes
fout = open('connectivity.bin','wb')
pickle.dump(bigbuffer, fout, pickle.HIGHEST_PROTOCOL)
fout.close()

# Let's save the record number, because may be very useful as indices,
# instead of looking for RCHIDs in a list... too slow.
fout_recno = open('connectivity_Recno.bin','wb')
pickle.dump(bigbufferRecno, fout_recno, pickle.HIGHEST_PROTOCOL)
fout_recno.close()
