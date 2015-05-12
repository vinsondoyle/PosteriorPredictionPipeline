#! /bin/bash
#
# This script executes a task under the control of the 0mq worker.
# It is past an absolute file name as the only argument. The script
# should be able to function stand-alone for testing, or under
# worker control.
#
# What follows is an example of what might be done, but is really
# limited only to the scripting included. Any other scripting language
# could be used, even a binary program.

# Capture the input file from the argument list, and split it into
# the directory path part, and the basename part (name less extension).

FILE=$1
DIR=`dirname ${FILE}`
BASE=`basename ${FILE}`

# Maybe run multiprocess (on one node only!). Here we are going to run 16
# per task, so create a list with the local hostname appearing 16 times.
# Just append the name, with a separating ",", then trim off any final ",".

PROCS=16
HOSTNAME=`uname -n`
HOSTLIST=""
for i in `seq 1 ${PROCS}`; do
   HOSTLIST="${HOSTNAME},${HOSTLIST}"
done 
HOSTLIST=${HOSTLIST%,*}

# Here we set the command line to use. May have to be sensitive to
# "quoting hell" issues if it gets too fancy.
#MB=/usr/local/packages/mrbayes/3.2.1/Intel-13.0.0-openmpi-1.6.2-CUDA-4.2.9/bin/mb
CMD="mpirun -host ${HOSTLIST} -np ${PROCS} mb < ${FILE} > ${BASE}.mb.log"

cd $DIR

# For testing purposes, use "if false". For production, use "if true"

if true ; then
   # Clean out any previous run.
   rm -f *.[pt] *.log *.ckp *.ckp~ *.mcmc
   eval "${CMD}"
else
   echo "${CMD}"
   echo "Faking It On Hosts: ${HOSTLIST}"
   sleep 2
fi
