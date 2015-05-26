#!/bin/bash

if [ $1 == "help" ]
then
	echo "usage: subsampler.sh subsamplingRate ntax burnin"
fi
 
if [ $1 != "help" ]
then
	for i in *.p
	do
		head -n 2 $i >> $i"_sub"
		header=`expr 2 + $3`
		awk '{if (((count++)-'$header')%'$1'==0 && (count)-'$header'>0)print $0;}' $i >> $i"_sub"
	done

	for i in *.t
	do  
		taxa=`expr 5 + $2`
		head -n $taxa $i >> $i"_sub"
		header=`expr 5 + $2 + $3`
		awk '{if (((count++)-'$header')%'$1'==0 && (count)-'$header'>0) print $0;}' $i >> $i"_sub"
	done
	
	for i in *.t
	do
		mv $i $i"_old"
	done
	
	for i in *.p
	do
		mv $i $i"_old"
	done
	
	for i in *.p_sub
	do
		mv $i `basename $i "_sub"`
	done
	
	for i in *.t_sub
	do
		mv $i `basename $i "_sub"`
	done
fi
