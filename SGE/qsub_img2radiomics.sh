#!/bin/sh
#
# SGE options
#$ -S /bin/sh
#$ -V
#$ -N i2r
#$ -l mem_free=16G
#$ -l h_vmem=16G
#$ -pe smp 4
#$ -cwd

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
export PATH=$CONDA/envs:$PATH
export PATH=$C3D/bin/:$PATH

source $CONDA/etc/profile.d/conda.sh
conda activate i2r
python -m i2r -c PIPELINES/PIPELINE_EXAMPLE -v --log log_pipeline_example.out --new_log
