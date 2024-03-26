import pickle
import numpy as np
import sys
import os
import pandas as pd
from progress.bar import Bar


def Connectivity(inputfile):

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
  contents = pd.read_csv(inputfile)

  # It is better to store ID and nodes information in separate vectors
  # Determine the number of lines to create the approprate vectors
  # (substract the line of the header)
  numelements = len(contents)

  idsistecol = np.zeros(numelements, dtype=np.int32)
  fromnode = np.zeros(numelements, dtype=np.int32)
  tonode = np.zeros(numelements, dtype=np.int32)

  # the toelement vector does not refer to the system id, but to normal
  # indices of the system's vector
  toelement = np.zeros(numelements, dtype=np.int32)
  toelement[:] = -1

  idsistecol = contents['RCHID'].to_numpy()
  fromnode = contents['FNODE'].to_numpy()
  tonode = contents['TNODE'].to_numpy()


  # for each element of the network, determine the next element
  # downstream
  for j in range(numelements):
    tupindex = np.where(fromnode == tonode[j])
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
    # lists are not very efficient, but are practical because they can grow
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

  return (contents, bigbuffer, bigbufferRecno)


def TrackUpstream(contents, connectivity):  # new name: connectivity

  numelements = len(contents)

  idsistecol = np.zeros(numelements, dtype=np.int32)
  microarea = np.zeros(numelements, dtype=np.float32)

  # the toelement vector does not refers to the system id, but to normal
  # indices of the system's vector
  toelement = np.zeros(numelements, dtype=np.int32)
  toelement[:] = -1

  idsistecol = contents['RCHID'].to_numpy()
  microarea = contents['AREA'].to_numpy()

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

    drainnetwork_fid = []  # store an index
    drainnetwork_sid = []  # store the RCH_ID

    # We have to calculate the drainage area of each catchment

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

      # Every element of the list corresponds to one basin only.
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


  BasinArea = np.zeros(numelements, dtype=np.float32)
  for j in range(len(idsistecol)):
    accumArea = 0.
    OneNetwork = drainnetwork_sid[j]
    for micro_sid in OneNetwork:
      tup1 = np.where(micro_sid == idsistecol)
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

  return BasinArea



def RelativeImportance(contents, drainArea, connectRecno):

  # Read in catchment information
  numlines = len(contents)
  numcatchments = numlines

  arrID = np.zeros(numcatchments, dtype=np.int32)
  arrFlow =  np.zeros(numcatchments, dtype=np.float32)
  arrCatchArea = np.zeros(numcatchments, dtype=np.float32)
  arrRI = np.zeros(numcatchments, dtype=np.float32)

  arrID = contents['RCHID']
  arrCatchArea = contents['AREA']
  arrFlow = contents['FLOW']
          

  # Load the list that contains the surface of the basin
  drainArea = np.array(drainArea)

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

  out_contents = pd.DataFrame({
    "RCHID" : arrID,
    "RELIMP" : arrRI
  })

  out_contents.to_csv(fname_priority_text, index=False)
