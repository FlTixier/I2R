#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _CHECK_FOLDER:

The `CHECK_FOLDER` module verifies if the subfolders within a study folder are structured correctly for use with img2radiomics. Each subfolder should contain the required DICOM or NIfTI files organized in the structure expected by img2radiomics.

Folder Structure Requirements
-----------------------------

Subfolders within a study folder should follow the structure shown below:

.. image:: img/Struct_OK.jpg
   :alt: Correct folder structure for img2radiomics

Alternatively, subfolders can be organized in the following structure and then reorganized using the `REORGANIZE` module:

.. image:: img/Struct_Ready.jpg
	:width: 400
	:alt: Alternative folder structure for img2radiomics

Options
-------

The `CHECK_FOLDER` module can be configured with the following options:

- **verbose**: Enables or disables verbose output, providing more details during execution.
- **timer**: Enables or disables the timer, recording the module's execution time.
- **inputFolder**: Specifies the path to the main study folder containing subfolders with DICOM files.
- **with-segmentation**: Indicates if subfolders contain segmentation files. Set to `False` if only some subfolders contain segmentation files.
- **log**: Path to a log file for recording output details.
- **new_log_file**: Creates a new log file. If a log file with the same name already exists, it will be overwritten.

Example Usage
-------------

The example below demonstrates how to use the `CHECK_FOLDER` module to verify that each subfolder within a study folder is correctly structured:

.. code-block:: bash

    CHECK_FOLDER:  # Verify if subfolders within a study folder have the correct structure
    {
        inputFolder: /path/to/study_folder
        with-segmentation: False
        log: /path/to/logs/checkfolder.log
    }
"""

# Check if a folder has the correct structure to process the image analysis pipeline
#
# Usage: StructFolderCheck.py -i <inputfolder>
#        StructFolderCheck.py --log=<logfile> --new_log --verbose --no-segmentation
# Help: StructFolderCheck.py -h or --help
#
# This script verifies the structure of a specified folder for compatibility with img2radiomics.
# Options:
#   -h, --help               Show help and usage information.
#   -v, --verbose            Enable verbose output (False by default).
#   -i, --inputFolder        Specify the input folder containing DICOM images.
#       --no-segmentation    Specify if the input folder does not contain segmentation files.
#       --log                Redirect output to a log file.
#       --new_log            Overwrite previous log file if it exists.

import sys, getopt, os
from tqdm import tqdm
import glob
import re
from datetime import datetime
from utils import hprint_msg_box
from utils import hprint

def main(argv):
    inpath = ''
    verbose = False
    c = 1;
    log = ''
    new_log = False
    NoSegmentation = False
    
    try:
        opts, args = getopt.getopt(argv, "vhi:",["log=","new_log","verbose","help","inputFolder=","no-segmentation"])
    except getopt.GetoptError:
        print('StructFolderCheck.py -i <inputfolder>',flush=True)
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME",flush=True)
            print("\tdStructFolderCheck.py\n",flush=True)
            print("SYNOPSIS",flush=True)
            print("\tStructFolderCheck.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>]\n",flush=True)
            print("DESRIPTION",flush=True)
            print("\tCheck if a folder has a correct structure to process the image analysis pipeline\n",flush=True)
            print("OPTIONS",flush=True)
            print("\t -h, --help: print this help page",flush=True)
            print("\t -v, --verbose: False by default",flush=True)
            print("\t -i, --inputFolder: input folder with Dicom images",flush=True)
            print("\t, --no-segmentation: input folder do not contain segmentations",flush=True)
            print("\t --log: stdout redirect to log file")
            print("\t --new_log: overwrite previous log file")

            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--log"):
            log= arg
        elif opt in ("--new_log"):
            new_log= True
        elif opt in ("--no-segmentation"):
            NoSegmentation = True 
        
    if log != '':
        if new_log:
            f = open(log,'w+')
        else:
            f = open(log,'a+')
        sys.stdout = f 
    
    if verbose:
        msg = (
            f"Cheking structure of: {inpath}\n"
            f"No segmentation: {str(NoSegmentation)}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose: {verbose}\n"
            )
        hprint_msg_box(msg=msg, indent=2, title=f"CHECK_FOLDER {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for patient in tqdm(glob.glob(inpath+"/*"),
                        ncols=100,
                        desc="Checking folder:",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
        
        patientID=os.path.basename(patient)
        if verbose:
            hprint(f"Processing {patientID}", patient)
       
        c=checkPatientFolderStructure(patient,verbose,log, NoSegmentation)
        if c==0:
            break;
    if c==0 :
        print("\033[33mFolder is NOT correctly structured for the image processing pipeline\033[0m",flush=True)
        print("Checking if the folder can be restructured using the script reoganize.py",flush=True)
        c=1
        for patient in tqdm(glob.glob(inpath+"/*"),
                            ncols=100,
                            desc="Checking folder:",
                            bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                            colour="yellow"):
        
            patientID=os.path.basename(patient)
            if verbose:
                hprint(f"Processing {patientID}", patient)
            
            c=checkPatientFolderStructure_Alternative(patient,verbose,log, NoSegmentation)
            if c==0:
                break;
        if c==0 :
            print("\033[31mFolder is NOT correctly structured to be restructed with reorganize.py\033[0m",flush=True)
            if log !='':
                sys.stdout = sys.__stdout__
                print("\033[31mFolder is NOT correctly structured to be restructed with reorganize.py\033[0m",flush=True)
                sys.stdout = f
            sys.exit()
        else:
            print("Folder is correctly structured to be restructed with reorganize.py",flush=True)
            if log !='':
                sys.stdout = sys.__stdout__
                print("Folder is correctly structured to be restructed with reorganize.py",flush=True)
                sys.stdout = f      
            sys.exit() 
    else:
        print("Folder is correctly structured for the image processing pipeline",flush=True)
        if log !='':
            sys.stdout = sys.__stdout__
            print("Folder is correctly structured for the image processing pipeline",flush=True)
            sys.stdout = f      

#return 1 if the folder has a valid structure
def checkPatientFolderStructure(patient,verbose,log,NoSegmentation):
    if log != '':
        f = open(log,'a+')
        sys.stdout = f
    Valid_structure=1
    for patient_subdirectory in glob.glob(patient+"/*"):        
        if os.path.isdir(patient_subdirectory):
            doc_list=os.listdir(patient_subdirectory)
            if not NoSegmentation: #Check for RTSTRUCT only if data are segmented
                if not "RTSTRUCT.dcm" in doc_list:  #subfolder contain a file RTSTRUCT.dcm
                    Valid_structure=0
                    if verbose:
                        print("\033[31mINCORRECT STRUCTURE FOUND FOR",patient,"\033[0m",flush=True)
                    return Valid_structure
                elif not os.path.isfile(os.path.join(patient_subdirectory,"RTSTRUCT.dcm")): #RTSTRUCT.dcm is a file not a folder
                    Valid_structure=0
                    if verbose:
                        print("\033[31mINCORRECT STRUCTURE FOUND FOR",patient,"\033[0m",flush=True)
                    return Valid_structure
            if not "DCM" in doc_list: #RTSTRUCT
                Valid_structure=0
                if verbose:
                    print("\033[31mINCORRECT STRUCTURE FOUND FOR",patient,"\033[0m",flush=True)
                return Valid_structure
            elif not os.path.isdir(os.path.join(patient_subdirectory,"DCM")):
                Valid_structure=0
                if verbose:
                    print("\033[31mINCORRECT STRUCTURE FOUND FOR",patient,"\033[0m",flush=True)
                return Valid_structure
    if verbose:
         print(patient,"... OK",flush=True)
    return 1
            
def checkPatientFolderStructure_Alternative(patient,verbose,log,NoSegmentation):
    if log != '':
        f = open(log,'a+')
        sys.stdout = f
        
    Alternative_valid_structure=1
    for patient_subdirectory in glob.glob(patient+"/*"):
        subdirectory=os.path.basename(patient_subdirectory)
        
        rtstruct_list=[f for f in os.listdir(patient) if os.path.isfile(os.path.join(patient,f))]
        #select index that match the name of the current subdirectory
        rtstruct_list_idx=[i for i, item in enumerate (rtstruct_list) if re.search(subdirectory,item, re.IGNORECASE)]
        if not NoSegmentation: #Check for RTSTRUCT only if data are segmented
            if len(rtstruct_list_idx) == 0:
                Alternative_valid_structure=0
                if verbose:
                    print("\033[31mINCORRECT STRUCTURE FOUND FOR",patient,"\033[0m",flush=True)
                return Alternative_valid_structure
            elif len(rtstruct_list_idx) > 1:
                Alternative_valid_structure=0
                if verbose:
                    print("\033[31mINCORRECT STRUCTURE FOUND FOR",patient,"\033[0m",flush=True)
                return Alternative_valid_structure
    if verbose:
       print(patient,"... OK",flush=True)
    return 1
            
            


if __name__ == "__main__":
    main(sys.argv[1:])         
