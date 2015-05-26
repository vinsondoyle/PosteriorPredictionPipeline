#!/bin/bash

for f in $(cat empDataDirectories)
do
cd $f
	for pfile in *.p
	do
	mv $pfile"_old" $pfile
	done
	for tfile in *.t
	do
	mv $tfile"_old" $tfile
	done
cd ../
done

