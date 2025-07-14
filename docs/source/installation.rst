============
Installation
============

Requirements
------------

1. **Miniconda/Anaconda (Version 24) with Python 3.11**:

   The software has been tested with Miniconda/Anaconda Version 24 and Python 3.11. Please ensure these are installed prior to proceeding:
    
   - [Anaconda installation instructions](https://docs.anaconda.com/free/anaconda/install/)
   - [Miniconda installation instructions](https://docs.anaconda.com/free/miniconda/miniconda-install/)
   - [Python website](https://www.python.org/)

2. **Convert 3D (c3d)**:
  
  Convert3D is optional for the `SPATIAL_RESAMPLING` module, which supports spatial resampling using either SimpleITK (sitk) or Convert3D as an alternative.
  
  - c3d can be downloaded from the [ITK-SNAP website](http://www.itksnap.org).

Installation Steps
------------------

1. **Copy the `img2radiomics` folder** to your home directory in the HPC environment or Linux computer.

2. **Create an environment for `image2radiomics`**:

   .. code-block:: bash

      conda create --name i2r python=3.11

3. **Install `image2radiomics` with pip**:

   .. code-block:: bash

      conda activate i2r
      pip install <path to img2radiomics>/<version>

   Alternatively, you can create the environment using the YAML files in the `img2radiomics` folder:

   - **Using `radiomics.yml`**:

     .. code-block:: bash

        conda env create --name radiomics --file=radiomics.yml

   - **Using `radiomics-with-TotalSegmentator.yml`** (This provides the option to use TotalSegmentator in the SEGMENTATION module):

     .. code-block:: bash

        conda env create --name radiomics --file=radiomics-with-TotalSegmentator.yml

   You can also create the environment manually. The following packages are required (tested versions in parentheses):

   - numpy (v1.25.2)
   - pandas (v2.0.3)
   - tqdm (v4.66.1)
   - pytorch (torch v2.0.1)
   - dicom2nifti (v2.4.8)
   - nibabel (v5.1.0)
   - rt-utils (v1.2.7)
   - SimpleITK (v2.3.1)
   - pyradiomics (v3.0.1)
   - totalsegmentator (v2.0.2)
   - openpyxl
   - opencv-python


Setting Up Automatic Processing
-------------------------------

Automatic processing deploys a model by creating a folder where data is processed automatically. After using Img2Radiomics to build a training set and a radiomics model, you can set up a folder to process new patient data similarly, enabling predictions using a previously built model.

1. **Follow steps 1 to 4** in the installation instructions.

2. **Edit the auto-submission script**: Edit `qsub_img2radiomics_auto.sh` (SGE), `sbatch_img2radiomics_auto.sh` (SLURM), or create your own script for automatic job submission.

3. **Create an input folder** where new data will be automatically processed.

   .. warning::

      Place only copies of data in this folder. **Data in this folder will be automatically removed after processing.**

4. **Create a working folder** for `img2radiomics` (e.g., `/$HOME/tmp`).

5. **Set up an automatic task with crontab**:

   - The list of crontab tasks can be accessed with `crontab -l` and removed with `crontab -e`.

   .. warning::

      The crontab list is only visible from the node used to submit the task. For reliability, run `init_folder_auto.py` from the login node.

   - Record the node used to submit the crontab task.

**Automatic Solution**

Run `./init_auto_folder.py` with the following options:

   - `--IMG2RADIOMICS <path to img2radiomics folder>`
   - `-m <minutes>`: Check the folder for new data every `<minutes>` minutes.
   - `--cdelay <# min>`: Only process folders created `<# min>` ago to avoid processing incomplete data.
   - `--tdelay <# sec>`: Process only folders with stable size over `<# sec>`.
   - `-i <input folder>`: Folder to check for new data.
   - `-o`: Working directory folder.
   - `-r`: Remove data from the pool after processing.
   - `--job_scheduler`: Choose between SGE, SLURM, and NONE (default SLURM).
   - `--job_name`: Script name for job submission.

**Example with SGE:**

.. code-block:: bash

    ./init_auto_folder.py -m 15 --job_scheduler SGE --cdelay 5 --tdelay 2 -i $HOME/data/newfiles_SGE -o $HOME/data/tmp/ -r --job_name qsub_img2radiomics_auto.sh --log $HOME/logs/crontab_img2radiomics_sge.log

**Example with SLURM:**

.. code-block:: bash

    ./init_auto_folder.py -m 15 --job_scheduler SLURM --cdelay 5 --tdelay 2 -i $HOME/data/newfiles_SLURM -o $HOME/data/tmp/ -r --job_name sbatch_img2radiomics_auto.sh --log $HOME/logs/crontab_img2radiomics_slurm.log

**Example without a job scheduler:**

.. code-block:: bash

    ./init_auto_folder.py -m 15 --job_scheduler NONE --cdelay 5 --tdelay 2 -i $HOME/data/newfiles -o $HOME/data/tmp/ -r --job_name img2radiomics_auto.sh --log $HOME/logs/crontab_img2radiomics.log

**Manual Solution**

a) Create necessary files:

   - **For SGE**: Create `path_to_qsub.txt` in the `img2radiomics` folder with the absolute path to `qsub`.
   - **For SLURM**: Create `path_to_sbatch.txt` in the `img2radiomics` folder with the absolute path to `sbatch`.
   - Create `path_to_img2radiomics.txt` with the absolute path to the img2radiomics program.

b) Use `crontab -e` and add the following line:

.. code-block:: bash

    */<every x minutes> * * * * SGE_ROOT=<path to SGE> <path to python3.11> <path to new_data_to_process.py> --IMG2RADIOMICS <path to img2radiomics> -i <input folder> -o <working folder> --job_scheduler <SGE or SLURM> -v --cdelay <minutes> --tdelay <seconds> --job_name <script name> >> <log file> 2>&1

**Example:**

.. code-block:: bash

    */10 * * * * SGE_ROOT=/cm/shared/apps/sge/sge-8.1.9/ /users/johndoe/miniconda3/bin/python3.11 /users/johndoe/img2radiomics/v0.8.2/new_data_to_process.py --IMG2RADIOMICS /users/johndoe/img2radiomics/v0.8.2/ -i /users/johndoe/data/newfiles/ -o /users/johndoe/data/tmp/ --job_scheduler SGE -v --cdelay 5 --tdelay 2 --job_name qsub_img2radiomics_auto.sh >> /users/johndoe/logs/crontab_img2radiomics.log 2>&1

`new_data_to_process.py` can be used with the following options:

- `-i`: Folder to check for new data to process.

   .. warning::
	
      Place only copies of data in this folder. **Data will be automatically removed after processing.**

- `-o`: Working directory folder.
- `--IMG2RADIOMICS`: Path to the img2radiomics folder.

- Optional:
  - `-v`: Verbose option.
  - `--cdelay <# min>`: Only process folders created `<# min>` ago.
  - `--tdelay <# sec>`: Only process folders with stable size over `<# sec>`.
  - `-r`: Remove data from the pool after processing.
  - `--job_scheduler`: Choose between SGE and SLURM (default SGE).
  - `--job_name`: Script name for job submission.

