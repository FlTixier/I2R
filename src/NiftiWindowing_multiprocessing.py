#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `I-WINDOWING` module allows users to perform image windowing by setting a window level (WL) and width (WW), or by using predefined windows for common clinical imaging protocols. This module includes several predefined windows sourced from Radiopaedia and Mayo Clinic for specific anatomical regions.

Predefined Windows
------------------

.. code-block:: text

    RADIOPAEDIA
    https://radiopaedia.org/
        head and neck
            'CT_brain' WW:80 WL:40
            'CT_subdural_1' WW:130 WL:50
            'CT_subdural_2' WW:300 WL:100
            'CT_subdural_3' WW:215 WL:75
            'CT_stroke_1' WW:8 WL:32
            'CT_stroke_2' WW:40 WL:40
            'CT_temporal_bones_1' WW:2800 WL:600
            'CT_temporal_bones_2' WW:4000 WL:700
            'CT_HN_soft_tissues_1' WW:350 WL:20
            'CT_HN_soft_tissues_2' WW:400 WL:60
            'CT_HN_soft_tissues_3' WW:375 WL:45

        chest
            'CT_lungs' WW:1500 WL:-600
            'CT_mediastinum' WW:350 WL:50

        abdomen
            'CT_AB_soft_tissues' WW:400 WL:50
            'CT_liver' WW:150 WL:30

        spine
            'CT_SP_soft_tissues' WW:250 WL:50
            'CT_bone' WW:1800 WL:400

    MAYO CLINIC        
    https://doi.org/10.1053/j.gastro.2022.06.066
        'CT_pancreas' WW:500 WL:50

Options
-------

The `I-WINDOWING` module supports the following options:

- **verbose**: Enable verbose output for detailed process information (default: False).
- **timer**: Enable a timer to record execution time (default: False).
- **inputFolder**: Path to the folder containing the input images.
- **outputFolder**: Path to save the windowed images.
- **outputFolderSuffix**: Adds a suffix to the `inputFolder` name to create the output folder.
- **log**: Path to a log file for saving detailed output information.
- **new_log_file**: Create a new log file, overwriting any existing file with the same name.
- **skip**: Path to a file listing subfolders in `inputFolder` to exclude from processing.
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **image_filename**: Name of the image file to apply windowing.
- **windowed_image_filename**: Name for the output windowed image.
- **suffix_name**: Suffix to add to the output image name. Overrides `windowed_image_filename` if specified.
- **window_width**: Range of intensity values within the image.
- **window_level**: Midpoint intensity value for the range.
- **window_name**: Name of the predefined window to apply.

Example Usage
-------------

The following example demonstrates how to use the `I-WINDOWING` module:

.. code-block:: bash

    I-WINDOWING:
    {
        inputFolder: /path/to/NIFTI_folder
        image_filename: img.nii.gz
        windowed_image_filename: img_w.nii.gz
        window_name: CT_pancreas
        log: /path/to/logs/windowing.log
    }

In this example:

- **inputFolder**: Specifies the folder containing the images to window.
- **image_filename** and **windowed_image_filename**: Define the input and output filenames for the windowed image.
- **window_name**: Uses the predefined `CT_pancreas` windowing values.
- **log**: Specifies the log file path to record processing details.


"""

# NiftiWindowing_multiprocessing applies windowing to NIfTI images using specified window level (--WL) and window width (--WW).
# Alternatively, predefined windows can be applied using the --preset option.
#
# RADIOPAEDIA Predefined Windows:
# https://radiopaedia.org/
#     head and neck
#         'brain' WW:80 WL:40
#         'subdural_1' WW:130 WL:50
#         'subdural_2' WW:300 WL:100
#         'subdural_3' WW:215 WL:75
#         'stroke_1' WW:8 WL:32
#         'stroke_2' WW:40 WL:40
#         'temporal_bones_1' WW:2800 WL:600
#         'temporal_bones_2' WW:4000 WL:700
#         'HN_soft_tissues_1' WW:350 WL:20
#         'HN_soft_tissues_2' WW:400 WL:60
#         'HN_soft_tissues_3' WW:375 WL:45
#     chest
#         'lungs' WW:1500 WL:-600
#         'mediastinum' WW:350 WL:50
#     abdomen
#         'AB_soft_tissues' WW:400 WL:50
#         'liver' WW:150 WL:30
#     spine
#         'SP_soft_tissues' WW:250 WL:50
#         'bone' WW:1800 WL:400
#
# MAYO CLINIC        
# https://doi.org/10.1053/j.gastro.2022.06.066
#     'pancreas' WW:500 WL:50
#
# Usage:
#     NiftiWindowing_multiprocessing.py -i <inputFolder> -o <outputFolder> [options]
# 
# Options:
#   -h, --help                       Show this help message and exit
#   -v, --verbose                    Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>  Input folder containing NIfTI images
#   -o, --outputFolder <outputFolder> Output folder to save windowed images
#       --img_name <image name>      Name of the image to apply the windowing (default: img.nii.gz)
#       --windowed_img_name <windowed image name> Name for the windowed image (default: w_img.nii.gz)
#   -e <suffix>                      Suffix to append to output image names (overrides windowed_img_name)
#       --WL <window level>          Window level for windowing
#       --WW <window width>          Window width for windowing
#       --preset <window name>       Name of a predefined window (refer to documentation for options)
#   -S <skip file path>              Path to a file listing filenames to skip
#       --include <include file path> Path to a file listing filenames to include (default: include all)
#       --log <log file path>        Redirect stdout to a log file
#       --new_log                    Overwrite an existing log file if it exists
#   -j, --n_jobs <number of jobs>    Number of simultaneous jobs (default: 1)
#
# Help:
#     NiftiWindowing_multiprocessing.py -h

import sys, getopt, os
from tqdm import tqdm
import glob
import multiprocessing
import nibabel as nib
from datetime import datetime
from utils import eprint
from utils import hprint_msg_box
from utils import hprint
from utils import format_list_multiline

def main(argv):
    inpath = ''
    outpath = ''
    dif_path=False #update to true if inpath != outpath, used to know if image need to be copied in a new folder
    verbose = False
    img = 'img.nii.gz'
    w_img= 'w_img.nii.gz'
    suffix = ''
    preset = ''
    w_level = '-5000'
    w_width = '-5000'
    n_jobs=1
    skip_file_name=''
    skip_files=[]
    include_file_name=''
    include_files=[]
    log = ''
    new_log = False
    
    try:
        opts, args = getopt.getopt(argv, "h:vi:o:j:S:e:",["log=","new_log","n_jobs=","verbose","help","inputFolder=","outputFolder=","img_name=","windowed_img_name=","WL=","WW=","preset=","skip=","include="])
    except getopt.GetoptError:
        print('NiftiWindowing_multiprocessing.py -i <inputfolder> -o <outputfolder> --WL <window level> --WW <windows width>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tNiftiWindowing_multiprocessing.py\n")
            print("SYNOPSIS")
            print("\tNiftiWindowing_multiprocessing.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>][-o|--outputFolder <outfolder>][--WL <window level>][--WW <window width>][--preset <window name>][-j|--n_jobs <number of simultaneous jobs>]\n")
            print("DESRIPTION")
            print("\tApply windowing to Nifti images using a window level (--WL) and a window width (--WW).")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with Nifti images")
            print("\t -o, --outFolder: output folder to save merged masks")
            print("\t --img_name: name of the image to apply the windowing (default: img.nii.gz)")
            print("\t --windowed_img_name: name to use to save the image after windowing (default: w_img.nii.gz)")
            print("\t -e: suffix to use in the name for output images (default \"\")")
            print("\t --WL: window level")
            print("\t --WW: window width")
            print("\t --preset: use a predifined window -- refer to manual for the list of predifined windows")
            print("\t -S, --skip: path to file with filenames to skip")
            print("\t --include: path to file with filenames to include (all files included by default)")
            print("\t --log: stdout redirect to log file")
            print("\t --new_log: overwrite previous log file")
            print("\t -j, --n_jobs: number of simultaneous jobs (default:1)")
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--WL"):
            w_level = arg
        elif opt in ("--WW"):
            w_width = arg
        elif opt in ("--preset"):
            preset = arg
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
        elif opt in ("--img_name"):
            img= arg   
        elif opt in ("--windowed_img_name"):
            w_img= arg
        elif opt in ("-e"):
            suffix= arg
    
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
            print("\033[33mWARNING! Input and output paths are identicals, windowed images will be saved in the input folder\033[0m",flush=True)
    else:
        dif_path=True
    
    if inpath == '':
        print("033[31mERROR! No input folder specify\033[0m",flush=True)
        sys.exit()
    
    if preset == '' and (w_level+w_width < -9999) :
         print("\033[31mERROR! You need to select a window with --preset or define manually the windows level and width with the options --WL and --WW\033[0m",flush=True)
         sys.exit()   
    
    if preset != '':
        w_width,w_level=windows_preset(preset) #update WL and WW with a window preset
   
    
    if suffix != '':
        w_img=os.path.splitext(os.path.splitext(os.path.basename(img))[0])[0]+"_"+suffix+".nii.gz"
    
    if verbose:
        msg =(
            f"Input path: {inpath}\n"
            f"Output path: {outpath}\n"
            f"Image to process: {img}\n"
            f"Windowed image name: {w_img}\n"
            f"Output suffix name: {suffix}\n"
            f"Window name: {preset}\n"
            f"Window level: {str(w_level)}\n"
            f"Window width: {str(w_width)}\n"
            f"n_jobs: {str(n_jobs)}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"Log: {str(log)}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose: {str(verbose)}\n"
            ) 
        hprint_msg_box(msg=msg, indent=2, title=f"I-WINDOWING {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    if n_jobs == 1:
        for patient in tqdm(glob.glob(inpath+"/*"),
                        ncols=100,
                        desc="Image Windowing",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
            windowing(patient,inpath,outpath,w_level,w_width,img,w_img,dif_path,skip_files,include_files,verbose,log)
    else:    
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(windowing,
                              [(patient,inpath,outpath,w_level,w_width,img,w_img,dif_path,skip_files,include_files,verbose,log) for patient in glob.glob(inpath+"/*")]),
                          ncols=100,
                          desc="Image Windowing",
                          bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                          colour="yellow")
            
def windows_preset(preset):
    presets = {
        'CT_brain': (80, 40),
        'CT_subdural_1': (130, 50),
        'CT_subdural_2': (300, 100),
        'CT_subdural_3': (215, 75),
        'CT_stroke_1': (8, 32),
        'CT_stroke_2': (40, 40),
        'CT_temporal_bones_1': (2800, 600),
        'CT_temporal_bones_2': (4000, 700),
        'CT_HN_soft_tissues_1': (350, 20),
        'CT_HN_soft_tissues_2': (400, 60),
        'CT_HN_soft_tissues_3': (375, 45),
        'CT_lungs': (1500, -600),
        'CT_mediastinum': (350, 50),
        'CT_AB_soft_tissues': (400, 50),
        'CT_liver': (150, 30),
        'CT_SP_soft_tissues': (250, 50),
        'CT_bone': (1800, 400),
        'CT_pancreas': (500, 50)
    }

    if preset in presets:
        w_width,w_level = presets[preset]
        return w_width,w_level
    else:
        return "\033[31mERROR Invalid windows preset\033[0m"
        sys.exit(1)



def windowing(patient,inpath,outpath,w_level,w_width,img_name,w_img_name,dif_path,skip_files,include_files,verbose,log):
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
        hprint(f"processing {patientID}",patient)
        
    if not os.path.exists(os.path.join(outpath,patientID)):
       os.makedirs(os.path.join(outpath,patientID))
   
    for patient_subdirectory in glob.glob(patient+"/*"):
       subdirectory=os.path.basename(patient_subdirectory)
       if verbose:
           print(patientID+": "+subdirectory,flush=True)
       
       if not os.path.exists(os.path.join(outpath,patientID,subdirectory)):
           os.makedirs(os.path.join(outpath,patientID,subdirectory))
       
       try: 
           # Load the NIfTI image
           img = nib.load(os.path.join(patient_subdirectory,img_name))
           data = img.get_fdata()
       except:
           print("\033[31mERROR reading "+os.path.join(patient_subdirectory,img_name),"\033[0m",flush=True)
           print("\033[31mSkipping "+patientID+" "+subdirectory+"\033[0m",flush=True)
           eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading image)")
           continue
       try: 
          # Apply windowing
          min_value = w_level - (w_width / 2)
          max_value = w_level + (w_width / 2)
          data[data < min_value] = min_value
          data[data > max_value] = max_value
       except:
          print("\033[31mERROR applying windowing (WL: "+w_level+" WW: "+w_width+")\033[0m",flush=True)
          print("\033[31mSkipping "+patientID+" "+subdirectory+"\033[0m",flush=True)
          eprint("Skipping "+patientID+" "+subdirectory+" (ERROR applying windowing)")
          continue 
       try:
           # Create a new NIfTI image with the modified data
           w_img=nib.Nifti1Image(data,affine=img.affine,header=img.header)
           nib.save(w_img,os.path.join(outpath,patientID,subdirectory,w_img_name)) 
       except:
           print("ERROR writing "+os.path.join(patient_subdirectory,w_img_name),flush=True)  
           print("\033[31mSkipping "+patientID+" "+subdirectory+"\033[0m",flush=True)
           eprint("Skipping "+patientID+" "+subdirectory+" (ERROR applying windowing)")
           continue
                        
if __name__ == "__main__":
    main(sys.argv[1:])    
