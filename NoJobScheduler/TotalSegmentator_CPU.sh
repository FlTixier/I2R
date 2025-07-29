#!/bin/sh

if [ "$1" = "dicom" ]; then
	TotalSegmentator -ot $1 -ml -i $2 -o $3 --roi_subset $4 -d cpu
else 
	TotalSegmentator -ot $1 -i $2 -o $3 --roi_subset $4 -d cpu
fi
