#!/bin/bash

count=1

for f in $(cat empDataDirectories)
do
base=`basename $f`
cd $base
java -jar PuMAv0.907c.jar puma.in > $base".puma.log"& 
echo $count $f
cd ../
if [ $count -eq 16 ]
then
wait
count=1
else
count=$((count+1))
fi
done

