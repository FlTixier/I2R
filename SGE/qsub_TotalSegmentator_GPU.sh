#!/bin/sh
#
# SGE options
#$ -S /bin/sh
#$ -V
#$ -N TotalSegmentator
#$ -l mem_free=120G
#$ -l h_vmem=120G
#$ -l gpu=1
#$ -pe smp 1
#$ -cwd
#
# Commands
#conda info
#python -u TotalSegmentator -i $2 -o $3 --roi_subset $4
if [ "$1" = "dicom" ]; then
	python -u TotalSegmentator -ot $1 -ml -i $2 -o $3 --roi_subset $4
else 
	python -u TotalSegmentator -ot $1 -i $2 -o $3 --roi_subset $4
fi
