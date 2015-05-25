#!/bin/bash

##This is to be run as an alternative to wq_mrc. This can be used on one node with 12 processors.


count=1

for f in $(cat empDataDirectories)
do
base=`basename $f`
cd $base
java -jar MrConverge1b2.5.jar mrc.conblock & 
echo $count $f
cd ../
if [ $count -eq 12 ]
then
wait
count=1
else
count=$((count+1))
fi
done


