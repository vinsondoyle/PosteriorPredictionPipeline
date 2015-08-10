#!/bin/bash

for f in *.nex
do
base=`basename $f .nex`
cd $base
rm MrConverge1b2.5.jar
rm PuMAv0.905.jar 
rm seq-gen 
rm subsamplerBurn3.2.sh	
rm *.tmp
cd SeqOutfiles
        for k in *.nex
        do
        baseK=`basename	$k .nex`
        cd $baseK
        rm MrConverge1b2.5.jar
	rm *.tmp
	if [ -f mrconverge.log ]
	then
	rm *_r*
	fi
	cd ../
	done
cd ../
cd ../
done
