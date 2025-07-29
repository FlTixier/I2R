#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The `REORGANIZE` module restructures data within a folder to prepare it for further processing with img2radiomics. This module organizes the data in a consistent format, ensuring compatibility with other processing modules.

**Note**: It’s recommended to run the `CHECK_FOLDER` module first to verify the folder structure before attempting reorganization. This helps avoid errors if the folder is incorrectly structured.

Options
-------

The `REORGANIZE` module accepts the following options:

- **verbose**: Enables verbose mode, providing additional details during execution (default: False).
- **timer**: Enables the timer to measure execution time (default: False).
- **inputFolder**: Specifies the path to the folder containing subfolders with DICOM or NIfTI files to reorganize.
- **outputFolder**: Specifies the path where the reorganized data will be saved. If omitted, `inplace` must be set to True.
- **outputFolderSuffix**: Adds a suffix to the name of `inputFolder` to create an output folder with a modified name (useful if `outputFolder` is not specified).
- **inplace**: Directly modifies the input folder instead of creating a new one. **Warning**: Use with caution, as any failure during reorganization may corrupt the data.
  
  .. warning::

      If the reorganization fails, `inplace` mode may corrupt the data in the input folder.

- **with-segmentation**: Indicates whether some subfolders contain segmentation files (default: True).
- **all-data-with-segmentation**: Specifies that all subfolders contain segmentation files (default: True).
- **log**: Specifies the path to a log file for recording detailed output information.
- **new_log_file**: Overwrites any existing log file with the same name.
- **skip**: Specifies a file containing a list of subfolders to exclude from reorganization.
- **include**: Specifies a file containing a list of subfolders to include in reorganization.
- **multiprocessing**: Specifies the number of CPU cores to use for parallel processing.

Example Usage
-------------

The following example demonstrates how to use the `REORGANIZE` module to restructure a study folder:

.. code-block:: bash

    REORGANIZE:
    {
        inputFolder: /path/to/DICOM_folder
        outputFolderSuffix: ready
        inplace: False
        log: /path/to/logs/reorganize.log
    }

In this example:

- The folder `/path/to/DICOM_folder` will be reorganized, and the output folder will be named `DICOM_folder_ready`.
- Data will be saved to a new folder (inplace is set to `False`).
- A log of the operation will be saved at `/path/to/logs/reorganize.log`.

"""


#The `reorganize_multiprocessing.py` script restructures folders containing DICOM files to match the directory layout expected by `dcm2nii.py`. This ensures that each patient’s data is organized consistently, allowing for streamlined processing in the image analysis pipeline.
#
#### Input Structure
#The input directory should have the following structure:
#
#    Folder
#     ├── Patient #1
#     │   ├── Sub-analysis #1
#     │   │   ├── #############.dcm
#     │   │   ├── #############.dcm
#     │   │   └── ...
#     │   ├── Sub-analysis #2
#     │   │   ├── #############.dcm
#     │   │   └── ...
#     │   └── ...
#     ├── Patient #2
#     │   └── ...
#     └── Patient #k
#
### Output Structure for `dcm2nii.py`
#After reorganization, the structure will look like this:
#
#    Folder
#     ├── Patient #1
#     │   ├── Sub-analysis #1
#     │   │   ├── DCM
#     │   │   │   ├── #############.dcm
#     │   │   │   └── ...
#     │   │   └── RTSTRUCT.dcm
#     │   ├── Sub-analysis #2
#     │   └── ...
#     ├── Patient #2
#     │   └── ...
#     └── Patient #k
# 
#
### Usage
#Run `reorganize_multiprocessing.py` with the following options:
#
#- **-i, --InPath**: Specify the input folder containing patient subfolders with DICOM files.
#- **-o, --OutPath**: Specify the output folder to save reorganized files. Required if `inplace` is `False`.
#- **--inplace**: If `True`, reorganizes files in the input folder directly without creating a new output folder.
#- **--log**: Specify the path to a log file to save output details.
#- **--new_log**: Overwrite an existing log file if one exists with the same name.
#- **-v, --verbose**: Enable verbose output for detailed processing information.
#- **--no-segmentation**: Specify if the input folder does not contain segmentation files (default: `False`).
#- **--all-segmentation**: Indicate that all subfolders contain segmentation files (default: `False`).
#- **-S, --skip**: Provide a file with a list of filenames to exclude from reorganization.
#- **--include**: Provide a file with a list of filenames to include in reorganization (all files included by default).
#- **-j, --n_jobs**: Set the number of CPU cores to use for parallel processing.
#
### Example Command
#
#To reorganize a folder with subfolders for each patient and save the result in a new directory:
#
#```bash
#python reorganize_multiprocessing.py -i /path/to/input_folder -o /path/to/output_folder --inplace=False --log /path/to/logfile.log
#Usage: reorganize_multiprocessing.py --InPath --OutPath --inplace=False
#Help: reorganize_multiprocessing.py  -h

import multiprocessing
import sys, getopt, os
import glob
from tqdm import tqdm
import shutil
import re
from datetime import datetime
from utils import hprint_msg_box
from utils import hprint

def main(argv):
    inpath = ''
    outpath = ''
    inplace = False
    verbose = False
    log = ''
    new_log = False
    n_jobs = 1
    skip_file_name=''
    include_file_name=''
    skip_files=[]
    include_files=[]
    NoSegmentation = False
    AllSegmentation = False

    try:
        opts, args = getopt.getopt(argv, "hi:o:vj:S:",["log=","new_log","InPath=","OutPath=","verbose","inplace","help","n_jobs=","skip=","include=","no-segmentation","all-segmentation"])
    except getopt.GetoptError:
        print('reorganize.py -i <inputfolder> -o <outputfolder> --inplace=False',flush=True)
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME",flush=True)
            print("\treorgnize\n",flush=True)
            print("SYNOPSIS",flush=True)
            print("\treorgnize.py [-h|--help][-v|--verbose][-i|--InPath <inputfolder>][-o|--OutPath <outfolder>][--inplace <bool>\n",flush=True)
            print("DESRIPTION",flush=True)
            print("\tReorganize folder with DICOM to work with structure expected for dcm2nii.py\n",flush=True)
            print("OPTIONS",flush=True)
            print("\t -h, --help: print this help page",flush=True)
            print("\t -v, --verbose: False by default",flush=True)
            print("\t -i, --InPath: input folder with Dicom images",flush=True)
            print("\t -o, --OutPath: output folder to save the organized files (if inplace=False)",flush=True)
            print("\t --inplace: if True use the input folder to regorganize patients' folders",flush=True)
            print("\t, --no-segmentation: input folder do not contains segmentations (default: False)",flush=True)
            print("\t, --all-segmentation: input folder contains segmentations for all data (default False)",flush=True)
            print("\t -S, --skip: path to file with filenames to skip",flush=True)
            print("\t --include: path to file with filenames to include (all files included by default)",flush=True)
            print("\t --log: stdout redirect to log file",flush=True)
            print("\t --new_log: overwrite previous log file")
            sys.exit()
        elif opt in ("-i", "--InPath"):
            inpath = arg
        elif opt in ("-o", "--OutPath"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--inplace"):
            inplace = True
        elif opt in ("--log"):
            log= arg
        elif opt in ("--new_log"):
            new_log= True
        elif opt in ("-S","--skip"):
            skip_file_name= arg
        elif opt in ("--include"):
            include_file_name= arg
        elif opt in ("-j", "--n_jobs"):
            n_jobs= int(arg)    
        elif opt in ("--no-segmentation"):
            NoSegmentation = True    
        elif opt in ("--all-segmentation"):
            AllSegmentation = True      
    
    if log != '':
        if new_log:
            f = open(log,'w+')
        else:
            f = open(log,'a+')
        sys.stdout = f 
        
        
    if skip_file_name != '':
        try:
            file= open(skip_file_name, 'r')
            skip_files = file.read().splitlines() 
        except:
            print("\033[31mERROR! Unable to read the skip file\033[0m",flush=True)  
    
    if include_file_name != '':
        try:
            file= open(include_file_name, 'r')
            include_files = file.read().splitlines() 
        except:
            print("\033[31mERROR! Unable to read the include file\033[0m",flush=True)  
    
    if verbose:
        msg = (
            f"Input path: {inpath}\n"
            f"Output path: {outpath}\n"
            f"Inplace: {inplace}\n"
            f"n_jobs: {n_jobs}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {skip_files}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {include_files}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"No segmentation: {NoSegmentation}\n"
            f"All data segmented: {AllSegmentation}\n"
            f"Verbose: {verbose}\n"
            )
        
        hprint_msg_box(msg=msg, indent=2, title=f"REORGANIZE {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not inplace and (inpath == outpath):
        print("ERROR! : input and output path must be different if inplace is not set to True",flush=True)
        sys.exit()
    else:
        if inplace:
            outpath = inpath
    
    if n_jobs == 1:
        for patient in tqdm(glob.glob(inpath+"/*"),
                        ncols=100,
                        desc="Reoganize",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
            reorganize(patient,inpath, outpath,inplace,skip_files,include_files,verbose,log, NoSegmentation,AllSegmentation)
    else:    
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(reorganize,
                              [(patient,inpath, outpath,inplace,skip_files,include_files,verbose,log, NoSegmentation,AllSegmentation) for patient in glob.glob(inpath+"/*")]),
                          ncols=100,
                          desc="Reorganize",
                          bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                          colour="yellow")
    
def reorganize(patient,inpath, outpath,inplace,skip_files,include_files,verbose,log, NoSegmentation,AllSegmentation):    
    if log != '':
        f = open(log,'a+')
        sys.stdout = f  
            
        patientID=os.path.basename(patient)
        
        if len(include_files) > 0: #if file to include are specify
            if patientID not in include_files: #if patient is to be excluded
                 if verbose:
                     print("\n"+patientID+" ("+patient+") is not in the list of patients to include",flush=True)
                 return 
        
        if len(skip_files) > 0: #if there are files to skip
             if patientID in skip_files:
                 if verbose:
                     print("\nskip "+patientID+" ("+patient+")",flush=True)
                 return
        
        #make directory for patient if output folder is different from input folder 
        if not os.path.exists(os.path.join(outpath,patientID)):
            os.makedirs(os.path.join(outpath,patientID))
        
        if verbose:
            hprint(f"Processing {patientID}", patient)         
            
        for patient_subdirectory in glob.glob(patient+"/*"):
            subdirectory=os.path.basename(patient_subdirectory)
            
            if os.path.isdir(patient_subdirectory): #sub directory is a folder not a file
                
                if verbose:
                    hprint("Subdirectory", patient_subdirectory)
            
                #make directory for subfolder if output folder is different from input folder 
                if not os.path.exists(os.path.join(outpath,patientID,subdirectory)):
                    os.makedirs(os.path.join(outpath,patientID,subdirectory))
            
                #make DCM subfolder if output folder is different from input folder 
                if not os.path.exists(os.path.join(outpath,patientID,subdirectory,"DCM")):
                    os.makedirs(os.path.join(outpath,patientID,subdirectory,"DCM"))
            
                for file in tqdm(glob.glob(patient_subdirectory+"/*"), position=0, leave=True):
                    if inplace:
                        try:
                            shutil.move(file,os.path.join(inpath,patientID,subdirectory,"DCM"))
                        except:
                            if os.path.isfile(file): #don't print the warning for a folder
                                print("\033[33mWARNING! the file "+file+" was not moved to DCM folder\033[0m",flush=True)
                    else:
                        try:
                            shutil.copy(file,os.path.join(outpath,patientID,subdirectory,"DCM"))
                        except:
                            print("\033[31mWARNING! the file "+file+" was not copied\033[0m")
                if not NoSegmentation: #Process RTSTRUCT only if data are segmented
                    rtstruct_list=[f for f in os.listdir(patient) if os.path.isfile(os.path.join(patient,f))]
                    #select index that match the name of the current subdirectory
                    rtstruct_list_idx=[i for i, item in enumerate (rtstruct_list) if re.search(subdirectory,item, re.IGNORECASE)]
                    if len(rtstruct_list_idx) == 0:
                        if AllSegmentation: #all data need to be segemented
                            print("\033[31mERROR! : RTSTUCT not found for the current subdirectory\033[0m",flush=True)
                            sys.exit()
                        else:
                            print("\033[31mWARNING! : No RTSTRUCT found for data "+file,"\033[0m",flush=True)
                    elif len(rtstruct_list_idx) > 1:
                        print("\033[31mERROR! : multiple RTSTRUCTs found for the current subdirectory\033[0m",flush=True)
                        sys.exit()
                    else:
                        rtstruct_name=rtstruct_list[rtstruct_list_idx[0]]
                        shutil.copy(os.path.join(inpath,patientID,rtstruct_name),os.path.join(outpath,patientID,subdirectory))
                        os.rename(os.path.join(outpath,patientID,subdirectory,rtstruct_name),os.path.join(outpath,patientID,subdirectory,"RTSTRUCT.dcm"))
                    if inplace:
                        os.remove(os.path.join(outpath,patientID,rtstruct_name))


            
if __name__ == "__main__":
    main(sys.argv[1:])   
