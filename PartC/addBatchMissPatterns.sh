#!/bin/bash

for f in $(cat empDataDirectories)
do
cp repMissPatternsVD.py $f
cd $f
base=`basename $f`
python repMissPatternsVD.py $base.nex 
mv SeqOutfiles simSeqOutfiles
mv SeqOutfiles_wMiss SeqOutfiles
cd ../
done
