#!/bin/bash
##Usage: Pass the name of the tab delimited file indicating the results of your modeltesting. It is assumed modeltesting was done in in MrModelTest or the results are 
##restricted to the 24 models compared in MrModelTest. The format of that file is two tab-separated columns. The first colum is the nexus file and the second is the model
##Models should be specified with a '+' between parameters. See below of the manual for examples.

if [[ $# -eq 0 ]] ; then
    echo 'you need to specify a tab delimited file indicating the best-fit model for each locus as an argument. Try again.'
    exit 0
fi


while read i
do
nex=`echo $i | awk {'print $1'}`
gene=`basename $nex .nex`
model=`echo $i | awk {'print $2'}`
mkdir $gene
cp $gene".nex" $gene
	if [ "$model" == "GTR" ]
	then
	cp GTR.bayesblock $gene
	elif [ "$model" == "GTR+G" ]
	then
	cp GTRG.bayesblock $gene
	elif [ "$model" == "GTR+I" ]
	then
	cp GTRI.bayesblock $gene
	elif [ "$model" == "GTR+I+G" ]
	then
	cp GTRIG.bayesblock $gene
	elif [ "$model" == "SYM" ]
	then
	cp SYM.bayesblock $gene
	elif [ "$model" == "SYM+G" ]
	then
	cp SYMG.bayesblock $gene
	elif [ "$model" == "SYM+I" ]
	then
	cp SYMI.bayesblock $gene
	elif [ "$model" == "SYM+I+G" ]
	then
	cp SYMIG.bayesblock $gene
	elif [ "$model" == "HKY" ]
	then
	cp HKY.bayesblock $gene
	elif [ "$model" == "HKY+G" ]
	then
	cp HKYG.bayesblock $gene
	elif [ "$model" == "HKY+I" ]
	then
	cp HKYI.bayesblock $gene
	elif [ "$model" == "HKY+I+G" ]
	then
	cp HKYIG.bayesblock $gene
	elif [ "$model" == "K80" ]
	then
	cp K80.bayesblock $gene
	elif [ "$model" == "K80+G" ]
	then
	cp K80G.bayesblock $gene
	elif [ "$model" == "K80+I" ]
	then
	cp K80I.bayesblock $gene
	elif [ "$model" == "K80+I+G" ]
	then
	cp K80IG.bayesblock $gene
	elif [ "$model" == "F81" ]
	then
	cp F81.bayesblock $gene
	elif [ "$model" == "F81+G" ]
	then
	cp F81G.bayesblock $gene
	elif [ "$model" == "F81+I" ]
	then
	cp F81I.bayesblock $gene
	elif [ "$model" == "F81+I+G" ]
	then
	cp F81IG.bayesblock $gene
	elif [ "$model" == "JC" ]
        then
	cp JC.bayesblock $gene
	elif [ "$model" == "JC+G" ]
        then
	cp JCG.bayesblock $gene
	elif [ "$model" == "JC+I" ]
        then
	cp JCI.bayesblock $gene
	elif [ "$model" == "JC+I+G" ]
        then
	cp JCIG.bayesblock $gene
	else
	echo "The model ( $model ) you have chosen for $gene is not one of the 24 available in the bayesblock files. A directory will be created for this locus, but there will not be a bayesblock file to run your empirical analysis."
	echo "You will need to create your own bayesblock file to add to this directory. Make sure to add the path to the bayesblock file to empDataList"
	fi
done < $1

for f in *.nex
do
base=`basename $f .nex`
cd $base
count=`ls -1 *bayesblock | wc -l`
  if [ $count != 0 ]
  then
  sed -i.tmp "s/data/$base/g" *bayesblock
  rm *bayesblock.tmp
  wD=`pwd`
  bb=`ls *bayesblock`
  echo $wD"/"$bb >> ../empDataList
  echo $base "is ready to be analyzed!"
  else
  echo "There is no bayesblock file in" $base
  fi
cd ../
done
