#!/bin/bash

for f in $(cat empDataDirectories)
do
base=`basename $f`
totaltrees=`grep "gen" $f/*.t | wc -l`
if [ $totaltrees != 100 ]
then
echo $base $totaltrees
fi
done
