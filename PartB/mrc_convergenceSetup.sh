#!/bin/bash

for f in $(cat empDataDirectories)
do
base=`basename $f`
cp mrc.conblock $f
cp MrConverge1b2.5.jar $f
sed -i.tmp "s/set filename=data/set filename=$base/g" $f"mrc.conblock"
done

for n in $(cat empDataDirectories)
do
cd $n
	count=1

	for f in *.t
	do
	baseT=`basename $f .nex.run$count.t`
	echo $f $baseT
	cp $f $baseT"_r"$count".t"
	((count ++))
	done

	count=1

	for g in *.p
	do
	baseP=`basename $g .nex.run$count.p`
	echo $f $baseP
	cp $g $baseP"_r"$count".p"
	((count ++))
	done
cd ../
done
