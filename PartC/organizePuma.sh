#!/bin/bash

for f in $(cat empDataDirectories)
do
mv $f"TREE/"*.dat $f"SeqOutfiles"
mv $f"TREE/"*.tree $f"TREEOutfiles"
done
