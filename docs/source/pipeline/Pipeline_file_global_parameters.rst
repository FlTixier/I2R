Global Parameters
-----------------

The **GLOBAL_PARAMETERS** module allows you to set default values for all modules in the pipeline file.

If an option is defined in both GLOBAL_PARAMETERS and a specific module, the value specified in that specific module will take precedence during execution.

Typically, **GLOBAL_PARAMETERS** can be used to:

- Enable or disable verbose mode with the `verbose` option.
- Enable or disable the timer to log the execution time of each module using the `timer` option.
- Select the job scheduler (either `SGE`, `SLURM` or `NONE`) with the `job_scheduler` option.
- Enable or disable multiprocessing and specify the number of cores to use with the `multiprocessing` option.

.. warning::

    When enabling multiprocessing in the pipeline file, it does not automatically request the specified number of cores when submitting a job. You need to configure this setting in the `qsub` (for **SGE**) or `sbatch` (for **SLURM**) script.

Example usage of the GLOBAL_PARAMETERS module:

.. code-block:: bash

    GLOBAL_PARAMETERS:
    {
        timer: True
        verbose: True
        job_scheduler: SLURM
        multiprocessing: 1  # No multiprocessing
        new_log_file: True #Create a new log file: if a log file with the same name already exists, it will be overwritten.
    }
