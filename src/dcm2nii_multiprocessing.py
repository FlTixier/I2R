#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `DCM2NII` module converts DICOM files into NIfTI format, making the data compatible for use in downstream image analysis pipelines. This module can handle folders containing segmentation files, and it includes options for selective processing and multi-core execution.

Options
-------

The `DCM2NII` module can be used with the following options:

- **verbose**: Enable or disable verbose mode for more detailed output (default: False).
- **timer**: Enable a timer to record the execution time (default: False).
- **inputFolder**: Path to the folder containing the DICOM files to be converted.
- **outputFolder**: Path to the folder where the converted NIfTI files will be saved.
- **outputFolderSuffix**: Adds a suffix to the input folder name to create an output folder.
- **regMatch**: Process only masks that match a specified regular expression (by default, all masks are processed).
- **with-segmentation**: Indicate whether the folders contain segmentation files (default: True).
- **all-data-with-segmentation**: Specify if all folders contain segmentation files (default: True).
- **log**: Path to a log file for saving detailed information about the conversion process.
- **new_log_file**: Create a new log file; if a file with the same name exists, it will be overwritten.
- **skip**: Path to a file listing subfolders in the input folder to exclude from the conversion.
- **include**: Path to a file listing subfolders in the input folder to include in the conversion (all subfolders included by default).
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.

Example Usage
-------------

The following example demonstrates how to use the `DCM2NII` module to convert a folder of DICOM files to NIfTI format:

.. code-block:: bash

    DCM2NII:
    {
        inputFolder: /path/to/DICOM_folder
        outputFolderSuffix: nii
        log: /path/to/logs/dcm2nii.log
    }

In this example:

- **inputFolder**: Specifies the folder containing DICOM files to be converted.
- **outputFolderSuffix**: Appends the suffix "nii" to the name of the `inputFolder` for the output directory.
- **log**: Saves a log file at the specified location, recording details of the conversion process.

"""

# Convert all DICOM images and RTSTRUCT segmentations into NIfTI images using the rt_utils library.
#
# Folder with DICOM images must be structured as follows:
#
# Folder
#  ├── Patient #1
#  │   ├── Sub-analysis #1
#  │   │   ├── DCM
#  │   │   │   ├── #############.dcm
#  │   │   │   └── ...
#  │   │   └── RTSTRUCT.dcm
#  │   ├── Sub-analysis #2
#  │   └── ...
#  ├── Patient #2
#  └── Patient #k
#
# Usage: dcm2nii_multiprocessing.py -i <DCM_Folder> -o <Nii_Folder> [options]
# Options:
#   -v, --verbose           Enable verbose output (default: False)
#   -m, --regMatch          Regular expression to filter masks (process all masks by default)
#   -S, --skip              Path to file listing subfolders to skip
#       --include           Path to file listing subfolders to include (all files included by default)
#       --no-segmentation   Specify if input folder does not contain segmentation files
#       --all-segmentation  Specify if all data has segmentation files (default: False)
#       --log               Path to log file for recording output details
#       --new_log           Overwrite existing log file if it exists
#   -j, --n_jobs            Number of simultaneous jobs for multiprocessing (default: 1)
# Help: dcm2nii_multiprocessing.py -h

import sys, getopt, os
import numpy as np
import glob
import dicom2nifti
from rt_utils import RTStructBuilder
import nibabel as nib
import re
from tqdm import tqdm
import multiprocessing
from datetime import datetime
from utils import eprint
from utils import hprint
from utils import hprint_msg_box
from utils import format_list_multiline
import concurrent.futures

def main(argv):
    dicom_path = ''
    nifti_path = ''
    mask_regMatch = ".*"
    verbose = False
    skip_file_name=''
    skip_files=[]
    include_file_name=''
    include_files=[]
    n_jobs=1
    log = ''
    NoSegmentation = False
    AllSegmentation = False
    new_log = False

    try:
        opts, args = getopt.getopt(argv, "hm:vi:o:j:S:",["log=","new_log","regMatch=","verbose","help","DCM_Folder=","Nii_Folder=","n_jobs=","skip=","include=","no-segmentation","all-segmentation"])
    except getopt.GetoptError:
        print('dcm2nii.py -i <inputfolder> -o <outputfolder>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME",flush=True)
            print("\tdcm2nii_multiprocessing.py\n",flush=True)
            print("SYNOPSIS",flush=True)
            print("\tdcm2nii_multiprocessing.py [-h|--help][-v|--verbose][-i|--DCM_folder <inputfolder>][-o|--Nii_folder <outfolder>][-m|--reg_Mask <regularexpression>][-j|--n_jobs <number of simultaneous jobs>]\n",flush=True)
            print("DESRIPTION",flush=True)
            print("\tConvert all DICOM images and RTSTRUCT segmentations in the DCM_Folder into Nifti images and save them in the Nii_folder\n",flush=True)
            print("OPTIONS",flush=True)
            print("\t -h, --help: print this help page",flush=True)
            print("\t -v, --verbose: False by default",flush=True)
            print("\t -i, --DCM_Folder: input folder with DICOM images",flush=True)
            print("\t -o, --Nii_Folder: output folder to save Nifti images",flush=True)
            print("\t -m, --regMatch: process only masks that match a regular expression (all masks by default)",flush=True)
            print("\t -S, --skip: path to file with filenames to skip",flush=True)
            print("\t --include: path to file with filenames to include (all files included by default)",flush=True)
            print("\t, --no-segmentation: input folder do not contain segmentations",flush=True)
            print("\t, --all-segmentation: input folder contains segmentations for all data (default False)",flush=True)
            print("\t --log: stdout redirect to log file",flush=True)
            print("\t --new_log: overwrite previous log file", flush=True)
            print("\t -j, --n_jobs: number of simultaneous jobs (default:1)",flush=True)
            sys.exit()
        elif opt in ("-i", "--DCM_Folder"):
            dicom_path = arg
        elif opt in ("-o", "--Nii_Folder"):
            nifti_path = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-m", "--regMask"):
            mask_regMatch = arg
        elif opt in ("-j", "--n_jobs"):
            n_jobs= int(arg)
        elif opt in ("-S","--skip"):
            skip_file_name= arg
        elif opt in ("--include"):
            include_file_name= arg
        elif opt in ("--log"):
            log= arg 
        elif opt in ("--new_log"):
            new_log= True
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
            f"Dicom path: {dicom_path}\n"
            f"Nifti path: {nifti_path}\n"
            f"Use mask names matching the regular expression: {mask_regMatch}\n"
            f"n_jobs: {n_jobs}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"No segmentation: {NoSegmentation}\n"
            f"All data segmented: {AllSegmentation}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            )
        
        hprint_msg_box(msg=msg, indent=2, title=f"DCM2NII {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    if dicom_path == '' or nifti_path == '':
        print("\033[31mERROR! Folders with DICOM and Nifti files need to be specified\033[0m", flush=True)
        sys.exit(2)
    elif dicom_path == nifti_path:
        print("\033[31mERROR! Input and output paths must be different\033[0m", flush=True)
        sys.exit(2)
    elif not os.path.isdir(dicom_path): # Check if dicom_path is a valid directory
        print(f"\033[31mERROR! The specified DICOM path '{dicom_path}' is not a valid directory.\033[0m", flush=True)
        sys.exit(2)
    else:        
        if n_jobs == 1:
            for patient in tqdm(glob.glob(dicom_path+"/*"),
                                ncols=100,
                                desc="Convert DICOM to NIFTI",
                                bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                                colour="yellow"):
                process_patient(patient,nifti_path,mask_regMatch, skip_files,include_files, verbose,log, NoSegmentation, AllSegmentation)
        else:    
            with multiprocessing.Pool(n_jobs) as pool:
                tqdm(pool.starmap(process_patient,
                                  [(patient,nifti_path,mask_regMatch,skip_files,include_files, verbose,log, NoSegmentation, AllSegmentation) for patient in glob.glob(dicom_path+"/*")]),
                              ncols=100,
                              desc="Convert DICOM to NIFTI",
                              bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                              colour="yellow")
        
def boolean_mask_to_3d_array(mask, value_true=1, value_false=0):
    # Get the shape of the boolean mask
    mask_shape = mask.shape
    # Create an empty 3D array with the same shape as the boolean mask
    array_3d = np.zeros((mask_shape[0], mask_shape[1], mask_shape[2]), dtype=int)
    # Set the values based on the boolean mask
    array_3d[mask] = value_true
    array_3d[~mask] = value_false
    return array_3d

def process_patient(patient,nifti_path,mask_regMatch,skip_files,include_files,verbose,log,NoSegmentation,AllSegmentation):
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
    if verbose:
        hprint(f"Processing {patientID}", patient)
    
    #make directory for patient in Nifti folder
    if not os.path.exists(os.path.join(nifti_path,patientID)):
        os.makedirs(os.path.join(nifti_path,patientID))
    
    
    for patient_subdirectory in glob.glob(patient+"/*"):
        subdirectory=os.path.basename(patient_subdirectory)
        if verbose:
                print(patientID+": "+subdirectory,flush=True)
    
        #make directory for subfolder
        if not os.path.exists(os.path.join(nifti_path,patientID,subdirectory)):
            os.makedirs(os.path.join(nifti_path,patientID,subdirectory))

        if verbose:
            print(patientID+": "+subdirectory+" image",flush=True)
        try:   
            if not convert_dicom_with_timeout(os.path.join(patient_subdirectory, "DCM"), os.path.join(nifti_path,patientID,subdirectory,"img.nii.gz")):
                continue  # Skip to the next `patient_subdirectory` if timeout
        except:
            print("\033[33mWARNING! Conversion to Nifti failed ("+patient_subdirectory+")"+" \u2014 Attempting conversion without checking SLICE_INCREMENT\033[0m",flush=True)
            try:
                dicom2nifti.settings.disable_validate_slice_increment()
                dicom2nifti.dicom_series_to_nifti(os.path.join(patient_subdirectory,"DCM"), os.path.join(nifti_path,patientID,subdirectory,"img.nii.gz"), reorient_nifti=True)
            except Exception as e:
                print("\033[31mERROR! Conversion to Nifti failed ("+patient_subdirectory+")\033[0m",flush=True)
                print("\033[31mSkipping image "+patientID+" "+subdirectory+"\033[0m",flush=True)
                eprint("Skipping "+patientID+" "+subdirectory+" (ERROR Conversion to Nifti failed)")
                continue
   
        if not NoSegmentation: #Process RTSTRUCT only if data are segmented
            print(patientID+": "+subdirectory+" masks",flush=True)
            if os.path.exists(os.path.join(patient_subdirectory,"RTSTRUCT.dcm")):
                try:
                    rtstruct=rtstruct_with_timeout(
                        dicom_series_path=os.path.join(patient_subdirectory, "DCM"),
                        rt_struct_path=os.path.join(patient_subdirectory, "RTSTRUCT.dcm"),
                        warn_only=False,
                        timeout_duration=60  # Set the timeout duration as needed
                        )
                except:
                    print("\033[33mWARNING! RTStructBuilder failed ("+patient_subdirectory+") \u2014 Attempting with warn only on\033[0m",flush=True)
                    try:
                        rtstruct=rtstruct_with_timeout(
                            dicom_series_path=os.path.join(patient_subdirectory, "DCM"),
                            rt_struct_path=os.path.join(patient_subdirectory, "RTSTRUCT.dcm"),
                            warn_only=True,
                            timeout_duration=60  # Set the timeout duration as needed
                            )

                    except Exception as e:
                        print("\033[31mERROR! RTStructBuilder failed ("+patient_subdirectory+")\033[0m",flush=True)
                        print(f"\033[31mSkipping segmentation for {patientID} {subdirectory}\033[0m",flush=True)
                        eprint(f"Skipping segmentation for {patientID} {subdirectory} (ERROR RTStructBuilder failed)")
                        continue
                try:
                    img = nib.load(os.path.join(nifti_path,patientID,subdirectory,"img.nii.gz"))
                except:
                    print("\033[31mERROR! Load Nifti image failed ("+os.path.join(nifti_path,patientID,subdirectory,"img.nii.gz")+")\033[0m",flush=True)
                    print(f"\033[31mSkipping segmentation for {patientID} {subdirectory}\033[0m",flush=True)
                    eprint(f"Skipping segmentation for {patientID} {subdirectory} (ERROR reading image))")
                    continue
        
                try:            
                    Struct_names= rtstruct.get_roi_names()
                    selected_idx=[i for i, item in enumerate(Struct_names) if re.search(mask_regMatch, item)]
                    for el in selected_idx:
                        if not Struct_names[el] in ['Origin','origin']:
                            Mask_array = rtstruct.get_roi_mask_by_name(Struct_names[el])
                            Mask_array = boolean_mask_to_3d_array(Mask_array, 1, 0)
                            Mask_array = np.rot90(Mask_array, -1)
                            newdataType=np.int8
                            Mask_array= Mask_array.astype(newdataType)
                            mask=nib.Nifti1Image(Mask_array,affine=img.affine,header=img.header)
                            nib.save(mask,os.path.join(nifti_path,patientID,subdirectory,"Mask_"+Struct_names[el].replace(" ", "_")+".nii.gz"))
                except Exception as e:
                    print("\033[31mERROR! Unable to get ROIs names\033[0m",flush=True)
            else: #No RSTRUCT
                if AllSegmentation: #all data need to be segemented
                    print("\033[31mERROR! : RTSTUCT not found for the current subdirectory\033[0m",flush=True)
                    eprint(f"Skipping segmentation for {patientID} {subdirectory} (ERROR!  RTSTUCT not found)")
                    continue
                else:
                    print("\033[33mWARNING! : No RTSTRUCT found for data "+os.path.join(nifti_path,patientID,subdirectory),"\033[0m",flush=True)


def convert_dicom_with_timeout(patient_subdirectory, nifti_output, reorient=True, timeout_duration=60):
    """Attempt to convert DICOM to Nifti with a specified timeout."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(dicom2nifti.dicom_series_to_nifti, patient_subdirectory, nifti_output, reorient_nifti=reorient)
        try:
            future.result(timeout=timeout_duration)
            return True  # Conversion succeeded
        except concurrent.futures.TimeoutError:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR! Conversion to Nifti timed out ({patient_subdirectory})", flush=True)
            eprint(f"Skipping {patient_subdirectory} (ERROR! Conversion to Nifti timed out)")
            return False  # Conversion failed due to timeout
        
def rtstruct_with_timeout(dicom_series_path, rt_struct_path,warn_only=False, timeout_duration=60):
    """Attempt to create an RTStruct with a specified timeout and optional warn_only behavior."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(
            RTStructBuilder.create_from,
            dicom_series_path,
            rt_struct_path,
            warn_only=warn_only  # Pass warn_only as a keyword argument
        )
        try:
            return future.result(timeout=timeout_duration)  # Return RTStructBuilder result if successful
        except concurrent.futures.TimeoutError:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR! RTStructBuilder creation timed out ({rt_struct_path})", flush=True)
            return None  # Return None if timed out
    
if __name__ == "__main__":
    main(sys.argv[1:])         
