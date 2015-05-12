#!/bin/bash
##USAGE: This script will create a generic model table file to be used by setupMB.sh. This is for those of you that do not want to bother will model testing
##and would rather just use a prespecified model of your choice. Pass the model as an argument. Just make sure you follow the formatting rules outlined
##in the usage statement in setupMB.sh


if [[ $# -eq 0 ]] ; then
    echo 'you need to specify a model that is covered by one of the bayesblock files. It needs to be in the format GTR+I+G, etc.  Try again.'
    exit 0
fi

for f in *nex
do
base=`basename $f .nex`
echo -e $base'\t'$1 >> genericModelTable.txt
done
