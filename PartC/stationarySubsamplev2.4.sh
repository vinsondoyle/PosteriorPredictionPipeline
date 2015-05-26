#!/bin/bash

for p in $(cat empDataDirectories)
do
base=`basename $p`
echo $p"/"$base".nex" >> empNexusList
done

for f in $(cat empNexusList)
do
base=`dirname $f`
cd $base
sed -i.tmp 's/ntax=/ntax = /g' $f
ntax=`grep "ntax" $f | awk {'print $4'}`
ntrees=`grep "Determining" mrconverge.log | awk {'print $5'}`
nburn=`grep "BURNIN" mrconverge.log | awk {'print $4'}`
samplRate=`expr $(( (ntrees - nburn)/24 ))`
stationaryTrees=`expr $(( (ntrees - nburn) ))`
if [[ $stationaryTrees -gt 100 ]]
then
remainingT=`expr $(( (ntrees - nburn) % 24 ))`
if [[ $remainingT -eq 0 ]]
then
samplRate=`expr $samplRate - 1` 
fi
samples=`expr $(( (ntrees - nburn)/samplRate ))`
while [[ $samples -ne 24 ]]
do 
if [[ $samples -gt 24 ]]
then
nburn=`expr $nburn + 1`
samplRate=`expr $(( (ntrees - nburn)/49 ))`
samples=`expr $(( (ntrees - nburn)/samplRate ))`
elif [[ $samples -lt 24 ]]
then
samplRate=`expr $samplRate - 1`
samples=`expr $(( (ntrees - nburn)/samplRate ))`
fi
done
else
  echo "Fewer than 100 trees in stationary distribution"
fi
#rm *_r*
cp ../subsamplerBurn3.2.sh .
./subsamplerBurn3.2.sh $samplRate $ntax $nburn
cd ../
done
