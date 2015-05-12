#!/bin/bash

##USAGE: ./setGenSampfreq.sh ngen samplefreq post/pre
##The arguments are: ngen - integer value of number of generations; samplefreq - integer value of sampling frequency; post/pre - post if you have already run setupMB.sh, pre if you have not

if [[ $# -lt 3 ]] ; then
    echo 'Expecting three arguments in this order: ngen samplefreq post/pre. See usage for details. Try again.'
    exit 0
fi


if [ $3 == "post" ]
then
  for f in $(cat empDataList)
  do
  sed -i.tmp "s/ngen=[^ ]* /ngen=$1 /g" $f
  sed -i.tmp "s/samplefreq=[^ ]*;/samplefreq=$2;/g" $f
  rm $f.tmp
  done
elif [ $3 == "pre" ]
then
  for p in *bayesblock
  do
  sed -i.tmp "s/ngen=[^ ]* /ngen=$1 /g" $p
  sed -i.tmp "s/samplefreq=[^ ]*;/samplefreq=$2;/g" $p
  rm $f.tmp
  done
else
  echo "you need to tell this script whether or not you have run setupMB.sh"
  echo 'if yes, enter "post". if no enter "pre"'
fi
