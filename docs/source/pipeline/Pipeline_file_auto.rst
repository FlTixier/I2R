.. _Gen_new_pipeline:

Automated Generation of Pipeline Files for Testing Datasets and Deployed Models
-------------------------------------------------------------------------------

PIPELINE files are primarily created for use with training datasets. If modules like `F-HARMONIZE` and `F-NORMALIZE` are employed, only statistics from the training set should be used to normalize or harmonize data from the testing set or new data in the deployed model.

The `gen_testing_pipeline.py` script can generate a new PIPELINE file, maintaining the structure of the training PIPELINE but adapted for processing data in the testing set or deployed model.

To run this script, you first need a `model folder` as described in the section above.

Options for the `gen_testing_pipeline.py` script:

- ``-m`` or ``--modelFolder``: Folder containing all relevant files derived from the training set, including the PIPELINE file, RADIOMICS CONFIGS file, and radiomics statistics.

- ``-s`` or ``--strategy``: Strategy (**`manual`**, suffix, or auto) to define the new input folder path. `Manual` (default) prompts for each new input folder path. `Suffix` prompts for the first path and uses `outputFolderSuffix` to define subsequent paths automatically. `Auto` sets the new input folder as `.` and `PREVIOUS_BLOCK_OUTPUT_FOLDER`; `img2radiomics` needs to be run with the `-i` option to specify the input folder for processing. The `auto` option is required for deploying a model.

- ``-p``: Adds a PREDICT module at the end of the generated PIPELINE file.

- ``suffix``: Sets the suffix for new log files (default is 'testing').

When running `gen_testing_pipeline.py`, you will be prompted for:

1. Select the PIPELINE file used on the training set.
2. Choose a name for the new PIPELINE file.
3. Provide a folder to save the new radiomics results.
4. Provide an Excel file with batch information for new patients.
5. Select the file with extracted radiomics features from the training set (final file after normalization and harmonization).
6. Select the file with batch information from the training set.
7. Select the file with radiomics statistics from the training set.
8. Select the pickle file with the radiomics model for predicting new patients (if ``-p`` is used).
