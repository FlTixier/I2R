#!/bin/sh
#
# SLURM options
#SBATCH --job-name=i2r_auto
#SBATCH --mem=20G
#SBATCH --ntask=2
#SBATCH --output=log_i2r_auto_slurm.out

VERSION="v0.8.4"
I2R="$HOME/img2radiomics/$VERSION"
CONDA="$HOME/anaconda3" 
C3D="$HOME/c3d-1.0.0-Linux-x86_64"

# Parse input parameters
for arg in "$@"; do
    if [ "$(echo "$arg" | grep '=')" ]; then
        eval "$arg"
    fi
done

# Check if the required parameters are provided
if [ -z "$inFolder" ]; then
    echo "Error: inFolder parameter is missing."
    echo "Usage: $0 inFolder=/path/to/pool/directory"
    exit 1
fi

# Check if the specified directory exists
if [ ! -d "$inFolder" ]; then
    echo "Error: $inFolder does not exist or is not a directory."
    exit 1
fi

input=${inFolder}

export PATH=$CONDA/bin:$PATH
export PATH=$CONDA/bin/conda:$PATH
export PATH=$CONDA/envs:$PATH
export PATH=$C3D/bin/:$PATH

#Initialize Conda
eval "$(conda shell.bash hook)"

conda activate i2r
cd $I2R
python -m i2r -c PIPELINES/PIPELINE_AUTO_EXAMPLE_SLURM -v --log log_pipeline_auto_example_slurm.out -i $input --new_log
