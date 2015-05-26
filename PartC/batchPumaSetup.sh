#!/bin/bash

for f in $(cat empDataDirectories)
do 
base=`basename $f`
cp puma.in $f
cp seq-gen $f
cp PuMAv0.907c.jar $f
sed -i.tmp "s/data/$base/g" $f"puma.in" 
done
