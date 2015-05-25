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

CMD="java -jar MrConverge1b2.5.jar ${FILE}"
cd $DIR

# For testing purposes, use "if false". For production, use "if true"

if true ; then
   eval "${CMD}"
else
   echo "${CMD}"
   echo "Faking It On Hosts: ${HOSTLIST}"
   sleep 2
fi
