Usage
=====

Image2Radiomics
---------------

Image2Radiomics operates with a :ref:`PIPELINE file <Pipeline_file>`, which contains all the instructions required to process images. This file defines a sequence of modules that are executed sequentially for each image in the folder to be processed. Examples are available in the `PIPELINES` folder.

Additionally, a `CONFIGS file` can be used to define configurations for radiomics feature extraction (see :ref:`Radiomics_configuration_file`). An example is available in the `RADIOMICS_CONFIGS` folder. It is also possible to directly use a pyradiomics configuration file with the `RADIOMICS` module (see :ref:`RADIOMICS module<RADIOMICS>`)

Image2Radiomics can be executed using the i2r.py program to compute radiomics features for all images in a folder, following the instructions specified in a pipeline configuration file. 

**`i2r.py` can be executed with the following options:**

**Required:**
	- ``-c <PIPELINE_FILE>``: Specifies the pipeline configuration file to use (see :ref:`Pipeline_file`).

**Optional:**
	- ``-v``: Enables verbose output.
	- ``--log <file.log>``: Saves the output to ``<file.log>``.
	- ``--new_log``: Overwrites the previous log file.
	- ``-i <input folder>``: If the ``<PIPELINE_FILE>`` does not specify an input folder (e.g., ``inputFolder: .``), the ``-i`` option is used to define the input folder.
  
  

**It is recommended to use a script to submit a job or run i2r**, as this allows you to define the computational resources, environment variables, and the :ref:`PIPELINE file <Pipeline_file>` to execute.

Examples of scripts are available in the `SGE` folder (for SGE clusters), the `SLURM` folder (for SLURM clusters), and the `NoJobScheduler` folder (for Linux systems without a job scheduler).

	- `qsub_img2radiomics.sh` (SGE cluster), `sbatch_img2radiomics.sh` (SLURM cluster), and `img2radiomics.sh` (No Job Scheduler) are examples for running img2radiomics on a dataset.
	- `qsub_img2radiomics_auto.sh` (SGE cluster), `sbatch_img2radiomics_auto.sh` (SLURM cluster), and `img2radiomics_auto.sh` (No Job Scheduler) are examples for deploying the model (see :ref:`next section <Init_Auto_Folder>`).

In these scripts, ensure that the variables `I2R`, `CONDA`, and `C3D` are correctly set to the paths of Imgage2Radiomics, Anaconda/Miniconda, and Convert3D, respectively.


**With SGE Job Scheduler**

You can submit the job using the following command:

.. code-block:: bash

    qsub SGE/qsub_img2radiomics.sh

**With SLURM Job Scheduler**

You can submit the job using the following command:

.. code-block:: bash

    sbatch SLURM/sbatch_img2radiomics.sh

**Without a Job Scheduler**

(Typically used on a personal computer)
You can run the script directly using the following command:

.. code-block:: bash

    sh NoJobScheduler/sbatch_img2radiomics.sh

.. _Init_Auto_Folder:

Init Auto Folder
----------------
	
`init_auto_folder.py` can be used to create a folder where data is automatically processed when new files are copied into it.

**Example with SGE Job Scheduler:**
   
.. code-block:: bash
	
    ./init_auto_folder.py -m 15 --job_scheduler SGE --cdelay 5 --tdelay 2 -i $HOME/data/newfiles_SGE -o $HOME/data/tmp/ -r --job_name SGE/qsub_img2radiomics_auto.sh --log $HOME/logs/crontab_img2radiomics_sge.log

**Example with SLURM Job Scheduler:**

.. code-block:: bash

    ./init_auto_folder.py -m 15 --job_scheduler SLURM --cdelay 5 --tdelay 2 -i $HOME/data/newfiles_SLURM -o $HOME/data/tmp/ -r --job_name SLURM/sbatch_img2radiomics_auto.sh --log $HOME/logs/crontab_img2radiomics_slurm.log

**Example without a Job Scheduler**

.. code-block:: bash

    ./init_auto_folder.py -m 15 --job_scheduler None --cdelay 5 --tdelay 2 -i $HOME/data/newfiles -o $HOME/data/tmp/ -r --job_name NoJobScheduler/img2radiomics_auto.sh --log $HOME/logs/crontab_img2radiomics.log

Create a Pipeline File
----------------------

Pipeline files for the training set need to be created manually based on the instructions in the :ref:`Pipeline_file` section. You can also edit the example pipeline files included in PIPELINES folder of `imgage2radiomics`.

To generate a pipeline file for a testing set that matches the instructions from the training set, use the `gen_testing_pipeline.py` tool. Pass the path to the folder containing the PIPELINE files and radiomics files from the training set using the **-r** flag. For details on the required contents of the reference folder, refer to the :ref:`Additional_info` section.

`gen_testing_pipeline.py` can also be used with the **-s** flag to select the strategy for defining new input and output paths for the testing set:

- **Manual** (default): Prompts you for all paths.
- **Suffix**: Prompts you for the first path and a path to store new results; all other paths will be generated automatically.
- **Auto**: Only prompts for the path to store new results. When using `auto` mode, run `img2radiomics` with the **-i** flag to specify the input folder. This mode is best suited for setting up a folder where new data is automatically processed (see :ref:`Init_Auto_Folder` for details).

If the model folder also contains a model built with scikit-learn saved as a `.pkl` file, you can use the **-p** flag to add a `PREDICT` module to the testing pipeline file (see :py:mod:`PREDICT module<predict>`).

**Example of using `gen_testing_pipeline.py`:**

.. code-block:: bash

    ./gen_testing_pipeline_file.py -r /path/to/reference/folder -s auto -p

