#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _MERGE_MASKS:

The `MERGE_MASKS` module enables the merging of multiple masks (segmentation files) using either regular expressions or lists of masks to add and subtract. This process creates a final segmentation mask suitable for radiomics analysis.

Options
-------

The `MERGE_MASKS` module accepts the following options:

- **verbose**: Enable verbose output for more detailed process information (default: False).
- **timer**: Enable a timer to record execution time (default: False).
- **inputFolder**: Path to the folder containing the input masks.
- **outputFolder**: Path to save the merged mask files.
- **outputFolderSuffix**: Adds a suffix to the `inputFolder` name to create the output folder.
- **log**: Path to a log file for saving detailed output information.
- **new_log_file**: Create a new log file, overwriting any existing file with the same name.
- **skip**: Path to a file listing subfolders in `inputFolder` to exclude from processing.
- **include**: Path to a file listing subfolders in `inputFolder` to include in processing (all subfolders included by default).
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **mask_name**: Name for the output merged mask file.
- **reg**: Regular expression to add all matching masks and subtract non-matching masks.
- **add**: List of specific masks to add.
- **sub**: List of specific masks to subtract.

Example Usage
-------------

The following examples demonstrate how to use the `MERGE_MASKS` module:

Using a regular expression to merge masks:

.. code-block:: bash

    MERGE_MASKS:
    {
        inputFolder: /path/to/NIFTI_folder
        mask_name: msk_111.nii.gz
        reg: Pancr*
        log: /path/to/logs/merge_masks.log
    }

Using specific lists of masks to add and subtract:

.. code-block:: bash

    MERGE_MASKS:
    {
        inputFolder: /path/to/NIFTI_folder
        mask_name: msk_111.nii.gz
        add: Mask_Pancreatic_Tumor.nii.gz,Mask_Pancreas.nii.gz
        sub: Mask_CBD.nii.gz,Mask_Arteries.nii.gz
        log: /path/to/logs/merge_masks.log
    }

In these examples:

- **inputFolder**: Specifies the folder containing mask files for merging.
- **mask_name**: Sets the filename for the merged output mask.
- **reg**: Adds masks matching "Pancr*" and subtracts those that don’t.
- **add** and **sub**: Explicitly define masks to add and subtract.
- **log**: Specifies the log file path to record processing details.
"""

## Merge NIfTI Masks by adding masks specified in the --add argument and subtracting masks listed in the --sub argument.
# Alternatively, masks can be merged using a regular expression to include all matching masks and exclude others.
#
# Usage:
#     NiftiMergeVolume_multiprocessing.py -i <inputFolder> -o <outputFolder> [options]
# 
# Options:
#   -h, --help                       Show this help message and exit
#   -v, --verbose                    Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>  Input folder containing NIfTI masks
#   -o, --outputFolder <outputFolder> Output folder to save the merged masks
#   -m, --mask_name <mask name>      Name for the merged mask file (default: "msk.nii.gz")
#       --reg <regex pattern>        Add masks that match the specified regular expression; subtract others
#       --add <mask list>            Comma-separated list of masks to add
#       --sub <mask list>            Comma-separated list of masks to subtract
#   -S <skip file path>              Path to a file listing filenames to skip
#       --include <include file path> Path to a file listing filenames to include (default: include all)
#       --log <log file path>        Redirect stdout to a log file
#       --new_log                    Overwrite an existing log file if it exists
#   -j, --n_jobs <number of jobs>    Number of simultaneous jobs (default: 1)
#
# Help:
#     NiftiMergeVolume_multiprocessing.py -h

import sys, getopt, os
from tqdm import tqdm
import glob
import multiprocessing
import shutil
import re
import nibabel as nib
import numpy as np
from datetime import datetime
from utils import eprint
from utils import hprint
from utils import hprint_msg_box
from utils import format_list_multiline

def main(argv):
    inpath = ''
    outpath = ''
    reg = ''
    add_list=[]
    sub_list=[]
    mask_name='msk.nii.gz'
    verbose = False
    n_jobs=1
    dif_path=False #update to true if inpath != outpath, used to know if image need to be copied in a new folder
    skip_file_name=''
    skip_files=[]
    include_file_name=''
    include_files=[]
    log = ''
    new_log = False

    try:
        opts, args = getopt.getopt(argv, "hm:vi:o:j:S:",["log=","new_log","reg=","n_jobs=","verbose","help","inputFolder=","outputFolder=","add=","sub=","reg=","mask_name=","skip=","include="])
    except getopt.GetoptError:
        print('NiftiMergeVolume_multiprocessing.py -i <inputfolder> -o <outputfolder> --add <list of masks> --sub <list of masks>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tNiftiMergeVolume_multiprocessing.py\n")
            print("SYNOPSIS")
            print("\tNiftiMergeVolume_multiprocessing.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>][-o|--outputFolder <outfolder>][--reg <regularexpression>][--add <list of masks>][--sub <list of masks>][-j|--n_jobs <number of simultaneous jobs>]\n")
            print("DESRIPTION")
            print("\tMerge NIfTI Masks by adding masks in the --add argument and subtracting the masks in the --sub argument.")
            print("\tThis script can also be used with a regular expression to add masks that match the regular expression and subtract the other masks.\n")            
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with NIfTI images")
            print("\t -o, --outFolder: output folder to save merged masks")
            print("\t -m, --mask_name: name to use to save the merged masks (default: msk.nii.gz)")
            print("\t --reg: process only masks that match a regular expression (all masks by default)")
            print("\t --add: list of masks to add (names need to be separated by commas")
            print("\t --sub: list of masks to subtract (names need to be separated by commas")
            print("\t -S, --skip: path to file with filenames to skip")
            print("\t --include: path to file with filenames to include (all files included by default)")
            print("\t --log: redirect stdout to a log file")
            print("\t --new_log: overwrite previous log file", flush=True)
            print("\t -j, --n_jobs: number of simultaneous jobs (default:1)")
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--reg"):
            reg = arg
        elif opt in ("-j", "--n_jobs"):
            n_jobs= int(arg)
        elif opt in ("--add"):
            add_list= arg.split(',')
        elif opt in ("--sub"):
            sub_list= arg.split(',')
        elif opt in ("-S","--skip"):
            skip_file_name= arg
        elif opt in ("--include"):
            include_file_name= arg
        elif opt in ("--log"):
            log= arg
        elif opt in ("--new_log"):
            new_log= True    
        elif opt in ("-m"):
            mask_name= arg   
            
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
        
    if reg=='' and len(add_list)==0:
        print("\033[31mERROR! the option --reg or --add need to used to select masks to add\033[0m",flush=True)
        sys.exit()   
    
    if reg!='' and (len(add_list)>0 or len(sub_list)>0) :
        print("\033[31mERROR! the options --reg and --add/--sub cannot be used in the same time\033[0m",flush=True)
        sys.exit()
        
    if verbose:
        msg = (
        f"Input path: {inpath}\n"
        f"Output path: {outpath}\n"
            )
        if reg != '':
            msg += f"Add mask names matching the regular expression and subtract the other masks: {reg}\n"
        if len(add_list) > 0:
            msg += f"Masks to add: {add_list}\n"
        if len(sub_list) > 0:
            msg += f"Masks to subtract: {sub_list}\n"
        msg += (
            f"n_jobs: {n_jobs}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose: {verbose}\n"
            )

        hprint_msg_box(msg=msg, indent=2, title=f"MERGE_MASKS {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if n_jobs == 1:
        for patient in tqdm(glob.glob(inpath+"/*"),
                        ncols=100,
                        desc="Merge masks",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
            merge_volume(patient,inpath,outpath,reg,add_list,sub_list,mask_name,dif_path,skip_files,include_files,verbose,log)
    else:    
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(merge_volume,
                              [(patient,inpath,outpath,reg,add_list,sub_list,mask_name,dif_path,skip_files,include_files,verbose,log) for patient in glob.glob(inpath+"/*")]),
                          ncols=100,
                          desc="Merge masks",
                          bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                          colour="yellow")
        
def merge_volume(patient,inpath,outpath,reg,add_list,sub_list,mask_name,dif_path,skip_files,include_files,verbose,log):
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
   
    if not os.path.exists(os.path.join(outpath,patientID)):
       os.makedirs(os.path.join(outpath,patientID))
   
    for patient_subdirectory in glob.glob(patient+"/*"):
       subdirectory=os.path.basename(patient_subdirectory)
       if verbose:
           print(patientID+": "+subdirectory,flush=True)
       
       if not os.path.exists(os.path.join(outpath,patientID,subdirectory)):
           os.makedirs(os.path.join(outpath,patientID,subdirectory))
       
       files_list=[f for f in os.listdir(patient_subdirectory) if os.path.isfile(os.path.join(patient_subdirectory,f))]

       img_idx=[i for i, item in enumerate (files_list) if re.search('.*img.*',item, re.IGNORECASE)]
              
       if len(img_idx) == 0:
           print("\033[31mERROR! : image not found for the current subdirectory\033[0m",flush=True)
           print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
           eprint("Skipping "+patientID+" "+subdirectory+" (ERROR Image Not Found)")
           continue
       else:
           if len(img_idx) > 1:
                print("\033[33mWARNING! : multiple images found for the current subdirectory (using affine and header information of the first one)\033[0m",flush=True)
                print("Images found:",flush=True)
                for idx in img_idx:
                     print(files_list[idx],flush=True)
           image_name=files_list[img_idx[0]]       
       
       #Copy image from the input folder
       if dif_path:
           try:
               shutil.copy(os.path.join(patient_subdirectory,image_name),os.path.join(outpath,patientID,subdirectory,image_name))
           except:
               print("\033[33mWARNING! The file "+image_name+" was not copied\033[0m",flush=True)
  
               
       img = nib.load(os.path.join(patient_subdirectory,image_name))
       mask_idx=[i for i, item in enumerate (files_list) if re.search('.*mask.*.nii.gz',item, re.IGNORECASE)]

       if reg != '':
           PositiveMasks= [i for i, item in enumerate([files_list[j] for j in mask_idx]) if re.search(reg, item, re.IGNORECASE)]
           NegativeMasks= [i for i, item in enumerate([files_list[j] for j in mask_idx]) if not re.search(reg, item, re.IGNORECASE)]
           

           if verbose:
               print("Masks to add: ", [files_list[int(mask_idx[int(i)])] for i in PositiveMasks])
               print("Masks to substract: ", [files_list[int(mask_idx[int(i)])] for i in NegativeMasks])
           
           PositiveMask_Added = np.zeros((img.header['dim'][1], img.header['dim'][2], img.header['dim'][3]))
           NegativeMask_Added = np.zeros_like(PositiveMask_Added)
   
           for i in PositiveMasks: 
               try:   
                   niftiAdd = nib.load(os.path.join(patient_subdirectory,files_list[int(mask_idx[int(i)])]))                    
                   dataAdd = niftiAdd.get_fdata()
                   PositiveMask_Added=PositiveMask_Added+dataAdd
                   PositiveMask_Added[PositiveMask_Added != 0] = 1
               except:
                   print("\033[31mERROR! Computing positive mask\033[0m",flush=True)
                   print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                   eprint("Skipping "+patientID+" "+subdirectory+" (ERROR computing positive mask)")
                   continue
       
           for i in NegativeMasks:
               try:
                    niftiAdd = nib.load(os.path.join(patient_subdirectory,files_list[int(mask_idx[int(i)])]))
                    dataAdd = niftiAdd.get_fdata()
                    NegativeMask_Added=NegativeMask_Added+dataAdd
                    NegativeMask_Added[NegativeMask_Added != 0] = 1
               except:
                   print("\033[31mERROR! Computing negative mask\033[0m",flush=True)
                   print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                   eprint("Skipping "+patientID+" "+subdirectory+" (ERROR computing negative mask)")
                   continue
       else:     #use --add and --sub arguments to compute the mask
           try:        
               PositiveMasks=[files_list.index(item) for item in add_list]
               NegativeMasks=[files_list.index(item) for item in sub_list]
               
               PositiveMask_Added = np.zeros((img.header['dim'][1], img.header['dim'][2], img.header['dim'][3]))
               NegativeMask_Added = np.zeros_like(PositiveMask_Added)
           except:
               print("\033[31mERROR! Mask not found\033[0m",flush=True)
               print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
               eprint("Skipping "+patientID+" "+subdirectory+" (ERROR mask not found)")
               continue

               
           for i in PositiveMasks: 
             try:    
                 niftiAdd = nib.load(os.path.join(patient_subdirectory,files_list[int(i)]))
                 dataAdd = niftiAdd.get_fdata()
                 PositiveMask_Added=PositiveMask_Added+dataAdd
                 PositiveMask_Added[PositiveMask_Added != 0] = 1
             except:
                 print("\033[31mERROR! Computing positive mask\033[0m",flush=True)
                 print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                 eprint("Skipping "+patientID+" "+subdirectory+" (ERROR computing positive mask)")
                 continue
               
           for i in NegativeMasks:
             try:
                  niftiAdd = nib.load(os.path.join(patient_subdirectory,files_list[int(i)]))
                  dataAdd = niftiAdd.get_fdata()
                  NegativeMask_Added=NegativeMask_Added+dataAdd
                  NegativeMask_Added[NegativeMask_Added != 0] = 1
             except:
                 print("\033[31mERROR! Computing negative mask\033[0m",flush=True)
                 print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                 eprint("Skipping "+patientID+" "+subdirectory+" (ERROR computing negative mask)")
                 continue
         
       try:
           FinalMask=PositiveMask_Added-NegativeMask_Added
           FinalMask[FinalMask != 1] = 0
       except:
           print("\033[31mERROR! Combining positive and negative masks\033[0m",flush=True)
           print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
           eprint("Skipping "+patientID+" "+subdirectory+" (ERROR Combining positive and negative masks)")
           continue
       try:
           mask=nib.Nifti1Image(FinalMask,affine=img.affine,header=img.header)
           nib.save(mask,os.path.join(outpath,patientID,subdirectory,mask_name)) 
       except:
           print("\033[31mERROR! Saving final mask\033[0m",flush=True)
           print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
           eprint("Skipping "+patientID+" "+subdirectory+" (ERROR Saving final mask)")
           continue

if __name__ == "__main__":
    main(sys.argv[1:])                   
