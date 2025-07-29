#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _F_HARMONIZE:

The F-HARMONIZE module allows for feature harmonization to correct batch effects due to variables like scanner, center, or other batch-related factors. Harmonization can be performed:

- Internally, using radiomics and batch data from input Excel files (`radiomics_filename` and `batch_filename`).
- Externally, using both the above files and additional radiomics and batch data from previously built models (specified using `radiomics_from_model_filename` and `batch_from_model_filename`).

.. image:: img/f-harmonize_folders.jpg
	:width: 400
	:alt: f-harmonize_folders.jpg

Modes of Harmonization
----------------------

- **Internal Mode (default)**: Harmonization occurs solely on the current radiomics file.
- **External Mode**: New data is harmonized with a reference batch from an external radiomics model.

When `mode` is set to `External`, harmonization is performed by merging the new data with data specified in `radiomics_from_model_filename`. If `ref_batch` is not specified, data from `radiomics_from_model_filename` will be used as the reference batch. Otherwise, the specified `ref_batch` is used as the reference batch (e.g., the name of a center).

The module saves results in an output folder (`outputFolder`), with results defaulting to the input folder if `outputFolder` is not specified. For external mode, a `modelFolder` must be provided to store relevant files for external data harmonization.

Options
-------

- **verbose**: Enable or disable verbose mode.
- **timer**: Enable or disable the timer to record execution time.
- **log**: Path to save logs.
- **new_log_file**: Overwrite log file if it already exists.
- **inputFolder**: Path to the input folder.
- **outputFolder**: Path to the output folder.
- **modelFolder**: Path to data from a previously built model (used with mode `External`).
- **radiomics_filename**: Name of the Excel file with radiomics results.
- **batch_file**: Name of the Excel file with batch information.
- **harmonized_radiomics_filename**: Name of the Excel file to store harmonized results (default: `harmonized_radiomics.xlsx`).
- **radiomics_from_model_filename**: External radiomics file used in building a model (for mode `External`).
- **batch_from_model_filename**: Batch information for `radiomics_from_model_filename` (for mode `External`).
- **estimates_filename**: Save neuroCombat estimates (works only in mode `Internal`). *DEPRECATED*
- **ref_batch**: Name of the batch to serve as reference.
- **covars**: Names of additional covariates to use (must be present in `batch_file` and `batch_from_model_filename`).
- **mode**: Specify harmonization mode: `Internal` (default) or `External`.

Batch File Structure
--------------------

Batch Excel files should include the following columns:

- **patientID**: Patient IDs matching those in the radiomics file.
- **sub_Analysis**: Sub-analysis column aligning with IDs in the radiomics file.
- **batch**: Batch information for harmonization (e.g., center or scanner).
- **Other covariates**: Optional columns for additional covariates (e.g., gender, age group, etc.).

.. image:: img/batch.jpg
	:width: 600
	:alt: batch.jpg

Example Usage
-------------

The following example demonstrates using F-HARMONIZE to perform harmonization with `center_1` as the reference batch from external radiomics data:

.. code-block:: bash

    F-HARMONIZE
    {
        inputFolder: /path/to/radiomics_results
        #no output folder specify: save output in the input folder
        modelFolder: /path/to/radiomics_model
        radiomics_from_model_filename: radiomics_train.xlsx
        batch_from_model_filename: batch_train.xlsx
        radiomics_filename: radiomics.xlsx
        batch_filename: batch.xlsx
        harmonized_radiomics_filename: harmonized_radiomics.xlsx
        mode: external
        covars: gender 
        ref_batch: center_1
        log: /path/to/logs/fharmonize.log
    }
"""

# feature_harmonization.py performs feature harmonization with neuroCombat,
# addressing batch effects related to scanner, center, or other batch factors.
#
#Perform feature harmonization with neuroCombat
#
# Usage:
#     feature_harmonization.py -i <inputFolder> -r <Radiomics_inputFile> -b <batchInfo_inputFile> -o <outputFolder>
#
# Options:
#   -h, --help                       Show this help message and exit
#   -v, --verbose                    Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>  Input folder containing radiomics and batch files
#   -o, --outputFolder <outputFolder> Output folder to save harmonized radiomics results
#   -r, --radiomicsFile <radiomicsFile> Name of the Excel file with radiomics features
#   -b, --batchFile <batchFile>      Name of the Excel file with batch information
#   -R, --harmonized_radiomicsFile <outputFile> Name for saving harmonized radiomics features
#   -E, --estimatesFile <estimatesFile> Pickle file for neuroCombat estimates; used in `writeEstimates` and `readEstimates` modes
#   -m, --modelFolder <modelFolder>  Folder with model results (for use with modes `writeEstimates_newData` or `readEstimates`)
#       --radiomics_from_model       Use this radiomics file for external harmonization; specify `ref_batch` if needed
#       --batch_from_model           Specify batch info file for `radiomics_from_model`
#       --mode                       Harmonization mode: `internal` (default) or `external` using external radiomics data
#       --ref_batch                  Name of the batch to use as the reference
#       --covars                     List of additional covariates for harmonization, separated by commas
#       --log <logFile>              Redirect stdout to a log file
#       --new_log                    Overwrite the previous log file if it exists
#
# Help:
#     feature_harmonization.py -h
#

import sys, getopt, os
import pandas as pd
import numpy as np
import re
import pickle
import traceback
from datetime import datetime
from utils import hprint_msg_box

sys.path.append(os.path.join(os.getcwd(),'_neuroCombat_'))
from _neuroCombat_ import neuroCombat
from _neuroCombat_ import neuroCombatFromTraining


def main(argv):
    modelpath = ''
    inpath = ''
    outpath = ''
    radiomics_filename = 'radiomics.xlsx'
    radiomics_from_model = ''
    batch_filename = 'batch.xlsx'
    batch_from_model = ''
    harmonized_radiomics_filename='radiomics_harmonized.xlsx'
    estimates_filename='estimates.pkl'
    ref_batch_name=None
    verbose = False
    mode = 'writeEstimates'
    log = ''
    covars_list = []
    new_log = False

    try:
        opts, args = getopt.getopt(argv, "vhi:o:b:r:R:E:m:M:",["log=","new_log","verbose","help","radiomicsFile=","harmonized_radiomicsFile=","estimatesFile=","batchFile=","inputFolder=","outFolder=","modelFolder=","ref_batch=","mode=","radiomics_from_model=","batch_from_model=","covars="])
    except getopt.GetoptError:
        print('feature_harmonization.py -i <inputFolder> -r <Radiomics_inputFile> -b <batchInfo_inputFile> -o <outputFolder>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tfeature_harmonization.py\n")
            print("SYNOPSIS")
            print("\tfeature_harmonization.py [-h|--help][-v|--verbose][--log <logFile>][-i|--inputFolder <inputfolder>][-o|--outputFolder <outputFolder>][-b|--batchFile <batchFileName>][-r|--radiomicsFile <radiomicsFileName>]\n")
            print("DESRIPTION")
            print("\tPerform feature harmonization with neuroCombat\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with radiomics and batch file")
            print("\t -o, --outFolder: output folder to save radiomics harmonization results")
            print("\t -m, --modelFolder: folder with model results (to be use with mode='writeEstimates_newData' or 'readEstimates')")
            print("\t -b, --batchFile: name of the excel file with batch information")
            print("\t -r, --radiomicsFile: name of the excel file with radiomics results")
            print("\t -R, --harmonized_radiomicsFile: name of the excel file to save harmonized radiomics features")
            print("\t -E, --estimatesFile: name of the pickel file with estimates from the ComBat harmonization. If mode is set to readEstimates, estimatesFile is read to harmonize new data. If mode is set to writeEstimates or writeEstimates_newData, estimates are saved for later use on new data")
            print("\t --radiomics_from_model: use this radiomic file to perform harmonization on new data. If this file is not harmonized radiomics features, a ref_batch needs to be specified. Otherwise, all the data from this file will be used as ref_batch")
            print("\t --batch_from_model: use this bacth file to specify batch info of the file in radiomics_from_model")
            print("\t --mode: specify if harmonization needs to be calculated using data from the radiomicsFile ('internal', default value) or data from another radiomics file ('external')")
            print("\t --ref_batch: name of the batch to use as a reference ")
            print("\t --covars: names of other outcome/covariates to take into account for harmonization. This option can contain a list of names separated by commas")
            print("\t --log: redirect stdout to a log file")
            print("\t --new_log: overwrite previous log file", flush=True)
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-r", "--radiomicsFile"):
            radiomics_filename = arg
        elif opt in ("-R", "--harmonized_radiomicsFile"):
            harmonized_radiomics_filename = arg  
        elif opt in ("-E", "--estimatesFile"):
            estimates_filename = arg                
        elif opt in ("-b", "--batchFile"):
            batch_filename = arg
        elif opt in ("-m", "--modelFolder"):
            modelpath = arg
        elif opt in ("--radiomics_from_model"):
            radiomics_from_model = arg
        elif opt in ("--ref_batch"):
            ref_batch_name = arg
        elif opt in ("--batch_from_model"):
            batch_from_model = arg
        elif opt in ("-M","--mode"):
            mode = arg
        elif opt in ("--covars"):
            covars_list=arg
            if covars_list != '':
                covars_list=covars_list.split(',')
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--log"):
            log= arg 
        elif opt in ("--new_log"):
            new_log= True  

    if log != '':
        if new_log:
            f = open(log,'w+')
        else:
            f = open(log,'a+')
        sys.stdout = f 

    if outpath == '':
        outpath = inpath
     
        
    if verbose:
        msg = (
            f"Input folder: {inpath}\n"
            f"Output folder: {outpath}\n"
            f"Model folder: {modelpath}\n"
            f"Radiomics file: {radiomics_filename}\n"
            f"Batch file: {batch_filename}\n"
            f"Estimators file: {estimates_filename}\n"
            f"Harmonized radiomics file: {harmonized_radiomics_filename}\n"
            f"Mode: {mode}\n"
            f"Radiomics from model file: {radiomics_from_model}\n"
            f"Batch from model file: {batch_from_model}\n"
            f"Reference batch name: {ref_batch_name}\n"
            f"Covariates: {covars_list}\n"
            f"Verbose: {verbose}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            )
        hprint_msg_box(msg=msg, indent=2, title=f"F-HARMONIZE {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Read radiomics file and remove dupplicates
    try:
        radiomics = pd.read_excel(os.path.join(inpath,radiomics_filename))
    except Exception as e:
            print(f"\033[31mERROR:\033[0m{e}",flush=True)
    duplicates = radiomics.duplicated(subset=['patientID', 'sub_Analysis'], keep='first')
    if verbose:
        if duplicates.any():
            print(f"\033[33mWARNING! Duplicates found and dropped in {radiomics_filename}\033[0m",flush=True)
            print(radiomics[duplicates][['patientID','sub_Analysis']],flush=True)
        else:
            print("No duplicates found in",radiomics_filename,flush=True)
    radiomics = radiomics.drop_duplicates(subset=['patientID', 'sub_Analysis'])
    radiomics_harmonized=radiomics.copy()

    # Read batch file and remove dupplicates
    try:
        batch = pd.read_excel(os.path.join(inpath,batch_filename))
    except Exception as e:
            print(f"\033[31mERROR:\033[0m{e}",flush=True)
    duplicates = batch.duplicated(subset=['patientID', 'sub_Analysis'], keep='first')
    if verbose:
        if duplicates.any():
            print(f"\033[33mWARNING! Duplicates found and dropped in {batch_filename}\033[0m",flush=True)
            print(batch[duplicates][['patientID','sub_Analysis']],flush=True)
        else:
            print("No duplicates found in",batch_filename,flush=True)
    batch = batch.drop_duplicates(subset=['patientID', 'sub_Analysis'])
    
    #check if element in covars list are in batch file
    if not all(el in batch.columns for el in covars_list):
        print(f"\033[31mERROR! {batch_filename} does not contain columns specified in --covars option ({covars_list})\033[0m",flush=True)
        sys.exit(1)
    
    #add batch to covariates
    if covars_list == '':
        covars_list = ['batch']
    else:
        covars_list.append('batch')
    covars_list= [item for item in covars_list if item != ''] #remove empty element
    if verbose:
        print("Batch and covariates:",covars_list,flush=True)

    
    #get only entries that match the entries on radiomic file
    batch=radiomics.merge(batch, on=['patientID','sub_Analysis'],how='left')[['patientID','sub_Analysis'] + covars_list]
    if verbose:
        print("Batch info:\n",batch,flush=True)

    #Check for missing values
    if batch.isna().sum().sum() > 0:
        print(f"\033[31mERROR! There are missing values in {batch_filename} file\033[0m", flush=True)
        if verbose:
            for index, row in batch.iterrows():
                if row.isna().any():
                   print(f"\033[31mMissing values found in row {index}:\033[0m")
                   print(row, flush=True)
        sys.exit(1)
        
    #get the list of radiomics features
    exclude_pattern = r'^(patientID|sub_Analysis)|diagnostic'
    columns_radiomics = [col for col in radiomics.columns if not re.match(exclude_pattern, col)]
        
    #create an array with radiomics features for combat
    radiomics_array = radiomics[columns_radiomics].values.astype('float64').T
            
    
    if mode in ('internal','INTERNAL','Internal'):
        try:
           #perform combat harmonization
           if ref_batch_name == 'None':
               ref_batch_name = None
           combat_harmonized = neuroCombat(dat=radiomics_array, covars=pd.DataFrame(batch[covars_list]),categorical_cols=[item for item in covars_list if item != 'batch'], batch_col='batch',ref_batch=ref_batch_name)
           #Save extimate
        except Exception as e:
            print(f"\033[31mERROR:\033[0m {e}",flush=True)
            print(traceback.format_exc(),flush=True)
            sys.exit()  
        if estimates_filename != '':
            try:
                with open(os.path.join(outpath,estimates_filename), "wb") as pickle_file:
                    pickle.dump(combat_harmonized["estimates"], pickle_file)
            except Exception as e:
                print(f"\033[31mERROR while saving estimates in {os.path.join(outpath,estimates_filename)}\033[0m",flush=True)
                print(f"\033[31mError:\033[0m {e}",flush=True)
        
        #Create a new data frame with harmonized features
        harmonized_features=pd.DataFrame(combat_harmonized["data"].T, columns=columns_radiomics)
        radiomics_harmonized[columns_radiomics] = harmonized_features[columns_radiomics]
    
    elif mode in ('external','EXTERNAL','Exernal'):
        #read radiomics from model and remove dupplicates
        try:
            radiomics_ref = pd.read_excel(os.path.join(modelpath,radiomics_from_model))
        except Exception as e:
                print(f"\033[31mERROR:\033[0m {e}",flush=True)
        duplicates = radiomics_ref.duplicated(subset=['patientID', 'sub_Analysis'], keep='first')
        if verbose:
            if duplicates.any():
                print("Duplicates found and dropped in",radiomics_from_model,flush=True)
                print(radiomics_ref[duplicates][['patientID','sub_Analysis']],flush=True)
            else:
                print("No duplicates found in",radiomics_from_model,flush=True)
        radiomics_ref = radiomics_ref.drop_duplicates(subset=['patientID', 'sub_Analysis'])
        # Read batch from model and remove dupplicates
        try:
            batch_ref = pd.read_excel(os.path.join(modelpath,batch_from_model))
        except Exception as e:
            print(f"ERROR: {e}",flush=True)       
        duplicates = batch_ref.duplicated(subset=['patientID', 'sub_Analysis'], keep='first')
        if verbose:
            if duplicates.any():
                print(f"\033[33mWARNING! Duplicates found and dropped in {batch_from_model}\033[0m",flush=True)
                print(batch_ref[duplicates][['patientID','sub_Analysis']],flush=True)
            else:
                print("No duplicates found in",batch_from_model,flush=True)
        batch_ref = batch_ref.drop_duplicates(subset=['patientID', 'sub_Analysis'])
        
        #check if element in covars list are in batch file
        if not all(el in batch_ref.columns for el in covars_list):
            print(f"\033[31mERROR! {batch_from_model} does not contain columns specified in --covars option ({covars_list})\033[0m",flush=True)
            sys.exit(1)
         
        #get only entries that match the entries on radiomic file
        batch_ref=radiomics_ref.merge(batch_ref, on=['patientID','sub_Analysis'],how='left')[['patientID','sub_Analysis'] + covars_list]

        #Check for missing values
        if batch_ref.isna().sum().sum() > 0:
            print(f"\033[31mERROR! There are missing values in {batch_from_model} file\033[0m", flush=True)
            sys.exit(1)  
        
        if str(ref_batch_name) not in ('None', ''):
            # Add the suffix '_ref' to all entries in the 'batch' column
            # This is done to not mix batch info from model and new data
            batch_ref['batch'] = batch_ref['batch'].apply(lambda x: x + '_ref')
            #Update ref batch name 
            ref_batch_name = ref_batch_name + '_ref'
        else: #all the data of model used as ref (should be used only if data are already normalized)
            batch_ref['batch'] = 'ref'
            ref_batch_name = 'ref'

        radiomics_all = pd.concat([radiomics_ref, radiomics], ignore_index=True)
        batch_all = pd.concat([batch_ref, batch], ignore_index=True)
       
        #create an array with radiomics features for combat
        radiomics_array_all = radiomics_all[columns_radiomics].values.astype('float64').T
        
        try:        
            combat_harmonized = neuroCombat(dat=radiomics_array_all, covars=pd.DataFrame(batch_all[covars_list]),categorical_cols=[item for item in covars_list if item != 'batch'], batch_col='batch',ref_batch=ref_batch_name)
            #Create a new data frame with harmonized features
            harmonized_features=pd.DataFrame(combat_harmonized["data"].T, columns=columns_radiomics)
            harmonized_features=harmonized_features[radiomics_ref.shape[0]:] #keep only the rows for new radiomics features
            harmonized_features.reset_index(drop=True,inplace=True)
            radiomics_harmonized[columns_radiomics] = harmonized_features[columns_radiomics]
        except:
            print("\033[31mERROR! neuroCombatFromTraining did not run properly\033[0m",flush=True)
            sys.exit()      
        
    #Save harmonized features
    try:
        radiomics_harmonized.to_excel(os.path.join(outpath,harmonized_radiomics_filename), index=False) 
    except Exception as e:
        print(f"\033[31mERROR:\033[0m{e}",flush=True)
        print(f"\033[31mERROR saving {os.path.join(outpath,harmonized_radiomics_filename)}\033[0m", flush=True)             


if __name__ == "__main__":
    main(sys.argv[1:])   
