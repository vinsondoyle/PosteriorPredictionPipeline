#!/bin/bash

##USAGE: ./setupPP_mb.sh empDataDirectoriesList ngen samplefreq nruns nchains
##assumes there is a line of the following format in a file ending in "bb": mcmc ngen=someNumber samplefreq=someNumber nruns=someNumber nchains=someNumber


for f in $(cat $1)
do
base=`basename $f`
cd $base
sed -i.tmp "/BEGIN/a Execute data.nex;" *.bb
cd SeqOutfiles
if [ $(ls */*.bb | wc -l) -eq 100 ]
then
	echo $base " Already processed"
else
	for n in *.nex
	do
	baseN=`basename $n .nex`
	mkdir $baseN
	cp $n $baseN
	cp ../*.bb $baseN
	cd $baseN
	sed -i.tmp "s/data/$baseN/g" *.bb
	sed -i.tmp "s/ngen=.*/ngen=$2 samplefreq=$3 nruns=$4 nchains=$5;/g" *.bb
	rm *.tmp
	cd ../
	done
fi 
cd ../
cd ../
done
