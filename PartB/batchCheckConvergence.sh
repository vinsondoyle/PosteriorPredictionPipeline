#!/bin/bash

for p in $(cat MRCLogList); do
python checkConvergence.py $p >> notConverged.txt
done
