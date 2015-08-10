#!/bin/bash

for f in *.nex
do
base=`basename $f .nex`
cd $base
cd SeqOutfiles
	for nex in *.nex
	do
	basenex=`basename $nex .nex`
	cd $basenex
	cp ../../../mrc.conblock .
	cp ../../../MrConverge1b2.5.jar .
	sed -i.tmp "s/set filename=data/set filename=$basenex/g" mrc.conblock
	cd ../
	done
cd ../
cd ../
done

for z in *.nex
do
basez=`basename $z .nex`
cd $basez
cd SeqOutfiles
	for n in *.nex
	do
	basen=`basename $n .nex`
	cd $basen
		count=1
	
		for q in *.t
		do
		baseT=`basename $q .nex.run$count.t`
		echo $q $baseT
		cp $q $baseT"_r"$count".t"
		((count ++))
		done
	
		count=1
	
		for g in *.p
		do
		baseP=`basename $g .nex.run$count.p`
		echo $g $baseP
		cp $g $baseP"_r"$count".p"
		((count ++))
		done
	cd ../
	done
cd ../
cd ../
done

