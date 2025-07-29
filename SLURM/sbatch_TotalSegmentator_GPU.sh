#!/bin/sh
#
# SLURM options
#SBATCH --job-name=GPUTotalSegmentator
#SBATCH --mem=60G
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --output=TotalSegmentator.log

# Commands
if [ "$1" = "dicom" ]; then
	TotalSegmentator -ot $1 -ml -i $2 -o $3 --roi_subset $4 -d gpu
else 
	TotalSegmentator -ot $1 -i $2 -o $3 --roi_subset $4 -d gpu
fi
