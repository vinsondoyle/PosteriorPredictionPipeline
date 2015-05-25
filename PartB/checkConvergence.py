#!/usr/bin/env python

###Usage: ./checkConvergence.py path/to/mrconverge.log
###Batch Usage: if you have a DataList file that contains the file paths to the mrconverge.log files, then run batchCheckConvergence.sh and look for the output in notConverged.txt
###Output: if the MaxBppCI for the statistic corresponding to the maximum Opt Burn value is greater than 0.1 then the MaxBppCI and the path to the mrconverge.log file will be output.
###Otherwise there not be any output unless you remove the hash marks from the lines at the bottom of the script pertaining to the else statement.

import os
import sys


if len(sys.argv) ==1:
	print 'you need the filename as an argument'
	sys.exit(-1)
else:
	file = sys.argv[1]

mrc = open(file, 'r')
line = mrc.readline()
while ( 'Opt Burn' not in line ):
  line = mrc.readline()
OptBurn = line.split()
OptBurn = map(int, OptBurn[2:4])
BurnCrit = OptBurn.index(max(OptBurn))
while ( 'MaxBppCI' not in line ):
  line = mrc.readline()
MaxBppCI = line.split()
MaxBppCIfloats = map(float, MaxBppCI[1:])
maxCI = MaxBppCIfloats[BurnCrit]
if maxCI >= .10:
  print maxCI,file
#else:
 # print "MaxBppCI is less than 0.1:", maxCI
