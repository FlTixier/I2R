#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `MASK_THRESHOLDING` module removes voxels from a mask if their intensity falls outside a specified range, allowing for selective masking based on intensity.

Options
-------

The `MASK_THRESHOLDING` module supports the following options:

- **verbose**: Enable verbose output for more detailed process information (default: False).
- **timer**: Enable a timer to record execution time (default: False).
- **inputFolder**: Path to the folder containing the input images.
- **outputFolder**: Path to save the thresholded mask files.
- **outputFolderSuffix**: Adds a suffix to the `inputFolder` name to create the output folder.
- **log**: Path to a log file for saving detailed output information.
- **new_log_file**: Create a new log file, overwriting any existing file with the same name.
- **skip**: Path to a file listing subfolders in `inputFolder` to exclude from processing.
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **image_filename**: Name of the image file to read for thresholding.
- **mask_filename**: Name of the mask file to apply the threshold.
- **suffix_name**: Suffix to append to the filename of the new thresholded mask.
- **min_threshold**: Minimum intensity threshold; voxels with lower intensity will be removed from the mask.
- **max_threshold**: Maximum intensity threshold; voxels with higher intensity will be removed from the mask.

Example Usage
-------------

The following example demonstrates how to use the `MASK_THRESHOLDING` module:

.. code-block:: bash

    MASK_THRESHOLDING:
    {
        inputFolder: /path/to/NIFTI_folder
        image_filename: img.nii.gz
        mask_filename: msk.nii.gz
        suffix_name: no_fat
        min_threshold: 0
        log: /path/to/logs/mask_thr.log
    }

In this example:

- **inputFolder**: Specifies the folder containing NIfTI files for thresholding.
- **image_filename** and **mask_filename**: Define the image and mask files to apply the thresholding.
- **suffix_name**: Adds the suffix "no_fat" to the thresholded mask filename.
- **min_threshold**: Sets the minimum voxel intensity to include.
- **log**: Specifies the log file path to record processing details.
"""


# Remove voxels from masks based on specified intensity thresholds.
# Voxels with intensities outside the defined min and max thresholds are removed.
#
#Remove values under and/or upper a threshold from masks
#
# Usage:
#     NiftiMaskThresholding_multiprocessing.py -i <inputFolder> -o <outputFolder> [options]
#
# Options:
#   -h, --help                       Show this help message and exit
#   -v, --verbose                    Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>  Input folder containing NIfTI images
#   -o, --outputFolder <outputFolder> Output folder to save thresholded masks
#   -e <suffix>                      Suffix for the output mask filenames (default: "mask_thresholding")
#       --min_thr <min threshold>    Minimum intensity threshold; remove voxels below this value
#       --max_thr <max threshold>    Maximum intensity threshold; remove voxels above this value
#       --img_name <image name>      Name of the image file to apply thresholding (default: "img.nii.gz")
#       --mask_name <mask name>      Name of the mask file to apply thresholding (default: "msk.nii.gz")
#   -S <skip file path>              Path to a file listing filenames to skip
#       --include <include file path> Path to a file listing filenames to include (default: include all)
#       --log <log file path>        Redirect stdout to a log file
#       --new_log                    Overwrite an existing log file if it exists
#   -j, --n_jobs <number of jobs>    Number of simultaneous jobs (default: 1)
#
# Help:
#     NiftiMaskThresholding_multiprocessing.py -h

import sys, getopt, os
import glob
import multiprocessing
from tqdm import tqdm
from datetime import datetime
import shutil
import nibabel as nib
import numpy as np
from utils import eprint
from utils import hprint_msg_box
from utils import hprint
from utils import format_list_multiline

def main(argv):
    inpath = ''
    outpath = ''
    verbose = False
    n_jobs=1              #nb of CPUs
    dif_path=False #update to true if inpath != outpath, used to know if image need to be copied in a new folder
    min_thr=sys.float_info.min
    max_thr=sys.float_info.max
    img_name="img.nii.gz"
    mask_name="msk.nii.gz"
    suffix = "mask_thresholding"
    skip_file_name=''
    skip_files=[]
    include_file_name=''
    include_files=[]
    log = ''
    new_log = False
 
    try:
        opts, args = getopt.getopt(argv, "hvi:o:j:e:S:M:I:",["log=","new_log","inputFolder=","outputFolder=","verbose","help","n_jobs=","--img_name=","--mask_name=","max_thr=","min_thr=","skip=","include="])
    except getopt.GetoptError:
        print("NiftiMaskThresholding_multiprocessing.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>][-o|--outputFolder <outfolder>][-e <suffix name for output imgage and mask>][--min_thr <min threshold>][--max_thr <max threshold>][-I|--img_name <image name>][-M|--mask_name <mask name>][-j|--n_jobs <number of simultaneous jobs>]\n")
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tNiftiMaskThresholding_mutiprocessing.py\n")
            print("SYNOPSIS")
            print("\tNiftiMaskThresholding_multiprocessing.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>][-o|--outputFolder <outfolder>][-e <suffix name for output imgage and mask>][--min_thr <min threshold>][--max_thr <max threshold>][-I|--img_name <image name>][-M|--mask_name <mask name>][-j|--n_jobs <number of simultaneous jobs>]\n")
            print("DESRIPTION")
            print("\tRemove values under and/or upper a threshold from masks\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with NIfTI images")
            print("\t -o, --outFolder: output folder to save Resampled NIfTI images")
            print("\t -e: suffix to use in the name for output masks (default \"mask_thresholding\")")
            print("\t -m, --mask_name: name of the mask to crop (default: msk.nii.gz)")
            print("\t --min_thr, remove voxel values under min_thr from the mask")
            print("\t --max_thr: remove voxel values upper max_thr from the mask")
            print("\t -S, --skip: path to file with filenames to skip whem processing resampling")
            print("\t --include: path to file with filenames to include (all files included by default)")
            print("\t --log: redirect stdout to a log file")
            print("\t --new_log: overwrite previous log file")
            print("\t -j, --n_jobs: number of simultaneous jobs (default:1)")
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-j", "--n_jobs"):
            n_jobs= int(arg)
        elif opt in ("-M, --mask_name"):
            mask_name= arg
        elif opt in ("-I, --img_name"):
            img_name= arg
        elif opt in ("--min_thr"):
             min_thr= arg   
        elif opt in ("--max_thr"):
            max_thr= arg   
        elif opt in ("-e"):
              suffix= arg
        elif opt in ("--log"):
             log= arg
        elif opt in ("--new_log"):
             new_log= True
        elif opt in ("-S","--skip"):
              skip_file_name= arg
        elif opt in ("--include"):
            include_file_name= arg
    
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
            print("\033[31mERROR! Unable to read the skip file\033[0m")

    if include_file_name != '':
        try:
            file= open(include_file_name, 'r')
            include_files = file.read().splitlines() 
        except:
            print("\033[31mERROR! Unable to read the include file\033[0m",flush=True) 
        
    if outpath =='':
        outpath = inpath
        if verbose:
            print("\033[33mWARNING! No output folder specify, results will be saved in the input folder\033[0m",flush=True)
    elif outpath==inpath:
        if verbose:
            print("\033[33mWARNING! Input and output paths are identicals, new masks will be saved in the input folder\033[0m",flush=True)
    else:
        dif_path=True
    
    if inpath == '':
        print("\033[31mERROR! No input folder specify\033[0m",flush=True)
        sys.exit()
        
    if verbose:
        msg =(
            f"Input path: {inpath}\n"
            f"Output path: {outpath}\n"
            f"Image name: {img_name}\n"
            f"Mask name: {mask_name}\n"
            f"Output suffix name: {suffix}\n"
            f"n_jobs: {str(n_jobs)}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"Remove from the mask voxels with values under than: {str(min_thr)}\n"
            f"Remove from the mask voxels with values upper than: {str(max_thr)}\n"
            f"Log: {str(log)}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose: {str(verbose)}\n"
            ) 
        hprint_msg_box(msg=msg, indent=2, title=f"MASK THRESHOLDING {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        
    if n_jobs == 1:
        for patient in tqdm(glob.glob(inpath+"/*"),
                        ncols=100,
                        desc="Masks Thresholding",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
            crop_volume(patient,inpath,outpath,min_thr,max_thr,img_name,mask_name,suffix,skip_files,include_files,dif_path,verbose,log)
    else:    
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(crop_volume,
                              [(patient,inpath,outpath,min_thr,max_thr,img_name,mask_name,suffix,skip_files,include_files,dif_path,verbose,log) for patient in glob.glob(inpath+"/*")]),
                          ncols=100,
                          desc="Masks Thresholding",
                          bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                          colour="yellow")

def crop_volume(patient,inpath,outpath,min_thr,max_thr,img_name,mask_name,suffix,skip_files,include_files,dif_path,verbose,log):
    if log != '':
        f = open(log,'a+')
        sys.stdout = f
    patientID=os.path.basename(patient)

    if len(include_files) > 0: #if file to include are specify
        if patientID not in include_files: #if patient is to be excluded
            if verbose:
                print("\033[33mWARNING \n"+patientID+" ("+patient+") is not in the list of patients to include\033[0m",flush=True)
            return 

    if len(skip_files) > 0: #if there are files to skip
         if patientID in skip_files:
             if verbose:
                 print("\033[33mWARNING\nskip "+patientID+" ("+patient+")\033[0m",flush=True)
             return
    
    
    output_mask_name=os.path.splitext(os.path.splitext(os.path.basename(mask_name))[0])[0]+"_"+suffix+".nii.gz"

    
    if verbose:
        hprint(f"processing {patientID}",patient)
    if not os.path.exists(os.path.join(outpath,patientID)):
       os.makedirs(os.path.join(outpath,patientID))
   
    for patient_subdirectory in glob.glob(patient+"/*"):
       subdirectory=os.path.basename(patient_subdirectory)
       if verbose:
           print(patientID+": "+subdirectory,flush=True)
       
       
       if not os.path.exists(os.path.join(outpath,patientID,subdirectory)):
           os.makedirs(os.path.join(outpath,patientID,subdirectory))

       #Copy image from the input folder
       if dif_path:
          try:
              shutil.copy(os.path.join(patient_subdirectory,img_name),os.path.join(outpath,patientID,subdirectory,img_name))
          except:
              print("\033[33mWARNING: the file "+img_name+" was not copied\033[0m",flush=True)
       
       try:
           img = nib.load(os.path.join(patient_subdirectory,img_name))
           msk = nib.load(os.path.join(patient_subdirectory,mask_name))
       except Exception as e:
           print("\033[31mERROR!\033[0m",e,flush=True)
           print("\033[31mSkipping "+patientID+" "+subdirectory+"\033[0m",flush=True)
           eprint("Skipping "+patientID+" "+subdirectory)
           continue 
 
       try:
           img_data=img.get_fdata().astype(float)
       except Exception as e:
            print("\033[31mERROR!\033[0m",e,flush=True)
            print("\033[31mSkipping "+patientID+" "+subdirectory+"\033[0m",flush=True)
            eprint("Skipping "+patientID+" "+subdirectory)
            continue 
       try:    
           msk_data = msk.get_fdata().astype(float)
           msk_data = np.where((img_data >= float(min_thr)) & (img_data <= float(max_thr)), msk_data, 0)  
       except Exception as e:
            print("\033[31mERROR!\033[0m",e,flush=True)
            print("\033[31mSkipping "+patientID+" "+subdirectory+"\033[0m",flush=True)
            eprint("Skipping "+patientID+" "+subdirectory)
            continue 
                   
       try:
           new_mask=nib.Nifti1Image(msk_data,affine=img.affine,header=img.header)
           nib.save(new_mask,os.path.join(outpath,patientID,subdirectory,output_mask_name)) 
       except:
           print("\033[31mERROR! Saving final mask\033[0m",flush=True)
           
           
           
if __name__ == "__main__":
    main(sys.argv[1:])
