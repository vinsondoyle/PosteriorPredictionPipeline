#! /bin/bash

FILE=$1
DIR=`dirname ${FILE}`
BASE=`basename ${FILE}`

# Maybe run multiprocess (on one node only!). Here we are going to run 16
# per task, so create a list with the local hostname appearing 16 times.
# Just append the name, with a separating ",", then trim off any final ",".

PROCS=8
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

# Clean out any previous run.

rm -f *.[pt] *.log *.ckp *.ckp~ *.mcmc

# For testing purposes, use "if false". For production, use "if true"

if true ; then
   eval "${CMD}"
else
   echo "${CMD}"
   echo "Faking It On Hosts: ${HOSTLIST}"
   sleep 2
fi
