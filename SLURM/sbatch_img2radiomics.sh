#!/bin/sh
#
# SLURM options
#SBATCH --job-name=i2r
#SBATCH --mem=16G
#SBATCH --ntasks=6
#SBATCH --output=log_i2r_slurm.out

VERSION="v0.8.4"
I2R="$HOME/img2radiomics/$VERSION"
CONDA="$HOME/anaconda3" 
C3D="$HOME/c3d-1.0.0-Linux-x86_64"

export PATH=$CONDA/bin:$PATH
export PATH=$CONDA/envs:$PATH
export PATH=$C3D/bin/:$PATH

#Initialize Conda
eval "$(conda shell.bash hook)"

conda activate i2r
python -m i2r -c PIPELINES/PIPELINE_EXAMPLE_SLURM -v --log log_pipeline_example.out --new_log
