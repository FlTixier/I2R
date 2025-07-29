#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `INTENSITY_RESAMPLING` module resamples voxel intensities in a NIfTI image using various methods, including a fixed number of bins, fixed bin width, linear scaling, robust scaling (linear scaling within a percentile range), or z-score normalization. The resampling can be performed on the entire image or only on voxels within a mask specified by the `mask_filename` option.

Options
-------

The `INTENSITY_RESAMPLING` module supports the following options:

- **verbose**: Enable or disable verbose mode for more detailed output (default: False).
- **timer**: Enable a timer to record execution time (default: False).
- **inputFolder**: Path to the folder containing the input NIfTI files.
- **outputFolder**: Path to the folder where the resampled images will be saved.
- **outputFolderSuffix**: Adds a suffix to the name of the `inputFolder` to create the output folder.
- **image_filename**: Specify the filename of the image to read.
- **mask_filename**: Specify the filename of the mask to apply during resampling (optional).
- **resampled_image_filename**: Specify the filename for the output resampled image.
- **method**: Resampling method to apply. Options: `binning_number` (fixed number of bins), `binning_width` (fixed bin width), `linear_scaling`, `robust_scaling` (linear scaling within a percentile range), or `zscore_normalization`.
- **n_bins**: Number of bins if `method` is `binning_number` (default: 256).
- **bin_width**: Bin width if `method` is `binning_width` (default: 25).
- **min_scaling**: Minimum value for scaling if using `linear_scaling` (default: 0).
- **max_scaling**: Maximum value for scaling if using `linear_scaling` (default: 1).
- **lower_bound**: Lower percentile bound for robust scaling (default: 2).
- **upper_bound**: Upper percentile bound for robust scaling (default: 98).
- **log**: Path to a log file for saving detailed output information.
- **new_log_file**: Create a new log file, overwriting any existing file with the same name.
- **skip**: Path to a file listing subfolders in `inputFolder` to exclude from processing.
- **include**: Path to a file listing subfolders in `inputFolder` to include in processing (all subfolders are included by default).
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **suffix_name**: Suffix to add to the filename of the resampled image.

Example Usage
-------------

The following example demonstrates how to use the `INTENSITY_RESAMPLING` module:

.. code-block:: bash

    INTENSITY_RESAMPLING:
    {
        inputFolder: /path/to/NIFTI_folder
        suffix_name: fb256
        method: binning_number
        n_bins: 256
        log: /path/to/logs/intensity_resampling.log
    }

In this example:

- **inputFolder**: Specifies the folder containing the NIfTI files to be resampled.
- **suffix_name**: Adds "fb256" as a suffix to the filenames of the resampled data.
- **method**: Sets the resampling method to `binning_number`, using a fixed number of bins.
- **n_bins**: Sets the number of bins to 256.
- **log**: Specifies the log file path to record processing details.
"""



# NiftiIntensityResampling_multiprocessing resamples voxel intensities in NIfTI images using various methods, including:
# a fixed number of bins, bin width, linear scaling, robust scaling (percentile range), or z-score normalization.
#
# Usage:
#     NiftiIntensityResampling_multiprocessing.py -i <inputFolder> -o <outputFolder> [options]
#
# Options:
#   -h, --help                       Show this help message and exit
#   -v, --verbose                    Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>  Input folder containing NIfTI images
#   -o, --outputFolder <outputFolder> Output folder for resampled images
#       --img_name <image name>      Name of the image to apply resampling (default: img.nii.gz)
#       --resampled_img_name <resampled image name> Name for saving the resampled image (default: r_img.nii.gz)
#   -e <suffix>                      Suffix to append to output image names (default: "")
#       --scale_min <minimum scale>  Minimum value for scaling (method must be 'linear_scaling')
#       --scale_max <maximum scale>  Maximum value for scaling (method must be 'linear_scaling')
#       --lower_bound <lower percentile> Lower percentile for 'robust_scaling'
#       --upper_bound <upper percentile> Upper percentile for 'robust_scaling'
#       --n_bins <number of bins>    Number of bins (method must be 'binning_number')
#       --bin_width <bin width>      Bin width (method must be 'binning_width')
#       --preset <window name>       Use a predefined window (refer to manual for available windows)
#   -S <skip file path>              Path to a file listing filenames to skip
#       --include <include file path> Path to a file listing filenames to include (default: include all)
#       --log <log file path>        Redirect stdout to a log file
#       --new_log                    Overwrite existing log file if it exists
#   -j, --n_jobs <number of jobs>    Number of simultaneous jobs (default: 1)
#
# Help:
#     NiftiIntensityResampling_multiprocessing.py -h

import sys, getopt, os
from tqdm import tqdm
import glob
import multiprocessing
import nibabel as nib
import numpy as np
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
    msk = ''
    r_img= 'r_img.nii.gz'
    suffix = ''
    method = ''
    n_bins = 256
    bin_width = 25
    scale_min = 0
    scale_max = 1
    lower_bound = 2
    upper_bound = 98
    n_jobs = 1
    skip_file_name= ''
    skip_files=[]
    include_file_name=''
    include_files=[]
    log = ''
    new_log = False

    try:
        opts, args = getopt.getopt(argv, "h:vi:o:j:S:e:",["log=","new_log","n_jobs=","verbose","help","inputFolder=","outputFolder=","img_name=","msk_name=","resampled_img_name=","scale_min=","scale_max=","lower_bound=","upper_bound=","n_bins=","bin_width=","method=","skip=","include="])
    except getopt.GetoptError as err:
        print(f'Error: {err.msg}')
        print('Usage: NiftiIntensityResampling_multiprocessing.py [-h|--help] [-v|--verbose] [-i|--inputFolder <inputfolder>] [-o|--outputFolder <outfolder>] [--img_name <image name>] [--resampled_img_name <resampled image name>] [-e <suffix>] [--scale_min <minimum scale>] [--scale_max <maximum scale>] [--lower_bound <lower percentile>] [--upper_bound <upper percentile>] [--n_bins <number of bins>] [--bin_width <bin width>] [--preset <window name>] [-S <skip file path>] [--include <include file path>] [--log <log file path>] [-j|--n_jobs <number of simultaneous jobs>]')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tNiftiIntensityResampling_multiprocessing.py\n")
            print("SYNOPSIS")
            print("\tNiftiIntensityResampling_multiprocessing.py [-h|--help] [-v|--verbose] [-i|--inputFolder <inputfolder>] [-o|--outputFolder <outfolder>] [--img_name <image name>] [--resampled_img_name <resampled image name>] [-e <suffix>] [--scale_min <minimum scale>] [--scale_max <maximum scale>] [--lower_bound <lower percentile>] [--upper_bound <upper percentile>] [--n_bins <number of bins>] [--bin_width <bin width>] [--preset <window name>] [-S <skip file path>] [--include <include file path>] [--log <log file path>] [-j|--n_jobs <number of simultaneous jobs>]\n")
            print("DESCRIPTION")
            print("\tResample voxel intensity of Nifti images")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with Nifti images")
            print("\t -o, --outputFolder: output folder to save resampled images")
            print("\t --img_name: name of the image to apply the resampling (default: img.nii.gz)")
            print("\t --resampled_img_name: name to use to save the image after resampling (default: r_img.nii.gz)")
            print("\t -e: suffix to use in the name for output images (default \"\")")
            print("\t --scale_min: minimum value for scaling (method needs to be 'linear_scaling')")
            print("\t --scale_max: maximum value for scaling (method needs to be 'linear_scaling')")
            print("\t --lower_bound: lower percentile to use for 'robust_scaling'")
            print("\t --upper_bound: upper percentile to use for 'robust_scaling'")
            print("\t --n_bins: number of bins (method needs to be 'binning_number')")
            print("\t --bin_width: size of bins (method needs to be 'binning_width')")
            print("\t --preset: use a predefined window -- refer to the manual for the list of predefined windows")
            print("\t -S, --skip: path to file with filenames to skip")
            print("\t --include: path to file with filenames to include (all files included by default)")
            print("\t --log: stdout redirect to log file")
            print("\t --new_log: overwrite previous log file")
            print("\t -j, --n_jobs: number of simultaneous jobs (default: 1)")
            sys.exit(0)
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--scale_min"):
            scale_min = float(arg)
        elif opt in ("--scale_max"):
            scale_max = float(arg)
        elif opt in ("--lower_bound"):
            lower_bound = float(arg)
        elif opt in ("--upper_bound"):
            upper_bound = float(arg)
        elif opt in ("--n_bins"):
            n_bins = int(arg)
        elif opt in ("--bin_width"):
            bin_width = float(arg) 
        elif opt in ("--method"):
            method = arg
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
        elif opt in ("--resampled_img_name"):
            r_img= arg
        elif opt in ("--msk_name"):
            msk=arg
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
            print("\033[33mWARNING! Input and output paths are identicals, resampleed images will be saved in the input folder\033[0m",flush=True)
    else:
        dif_path=True
    
    if inpath == '':
        print("\033[31mERROR! No input folder specify\033[0m",flush=True)
        sys.exit()
    
    
    if suffix != '':
        r_img=os.path.splitext(os.path.splitext(os.path.basename(img))[0])[0]+"_"+suffix+".nii.gz"
    
    if verbose:
        msg = (
            f"Input path: {inpath}\n"
            f"Output path: {outpath}\n"
            f"Image to process: {img}\n"
            f"Resampled image name: {r_img}\n"
            f"Output suffix name: {suffix}\n"
            f"{'Resampling will be performed using the entire image' if msk == '' else 'Resampling will be performed using values in the mask: ' + msk}\n"
            f"Method: {method}\n"
            )
        if method.lower() == 'linear_scaling':
            msg += (
                f"Min: {scale_min}\n"
                f"Max: {scale_max}\n"
                )
        elif method.lower() == 'binning_number':
            msg += f"Number of bins: {n_bins}\n"
        elif method.lower() == 'binning_width':
            msg += f"Bin width: {bin_width}\n"
        elif method.lower() == 'robust_scaling':
            msg += (
                f"Lower bound: {ordinal_suffix(lower_bound)} percentile\n"
                f"Upper bound: {ordinal_suffix(upper_bound)} percentile\n"
                )
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
        
        hprint_msg_box(msg=msg, indent=2, title=f"INTENSITY_RESAMPLING {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


    if n_jobs == 1:
        for patient in tqdm(glob.glob(inpath+"/*"),
                        ncols=100,
                        desc="Intensity Resampling",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
            resampling(patient,inpath,outpath,img,r_img,msk,method,scale_min,scale_max,lower_bound,upper_bound,n_bins,bin_width,dif_path,skip_files,include_files,verbose,log)
    else:    
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(resampling,
                              [(patient,inpath,outpath,img,r_img,msk,method,scale_min,scale_max,lower_bound,upper_bound,n_bins,bin_width,dif_path,skip_files,include_files,verbose,log) for patient in glob.glob(inpath+"/*")]),
                          ncols=100,
                          desc="Intensity Resampling",
                          bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                          colour="yellow")


def resampling(patient,inpath,outpath,img_name,r_img_name,msk_name,method,scale_min,scale_max,lower_bound,upper_bound,n_bins,bin_width,dif_path,skip_files,include_files,verbose,log):
    if log != '':
        f = open(log,'a+')
        sys.stdout = f
        
    patientID=os.path.basename(patient)
    
    if len(include_files) > 0: #if file to include are specify
        if patientID not in include_files: #if patient is to be excluded
            if verbose:
                print(f"\n{patientID} ({patient}) is not in the list of patients to include", flush=True)
            return 
    
    if len(skip_files) > 0: #if there are files to skip
         if patientID in skip_files:
             if verbose:
                 print(f"\nSkipping {patientID} ({patient})", flush=True)
             return

    if verbose:
        hprint(f"processing {patientID}",patient)

   
    if not os.path.exists(os.path.join(outpath,patientID)):
       os.makedirs(os.path.join(outpath,patientID))
   
    for patient_subdirectory in glob.glob(patient+"/*"):
       subdirectory=os.path.basename(patient_subdirectory)
       if verbose:
           print(f"{patientID}: {subdirectory}", flush=True)
       
       if not os.path.exists(os.path.join(outpath,patientID,subdirectory)):
           os.makedirs(os.path.join(outpath,patientID,subdirectory))
       
       try: 
           # Load the NIfTI image
           img = nib.load(os.path.join(patient_subdirectory,img_name))
           img_data = img.get_fdata()
       except FileNotFoundError:
            print(f"\033[31mERROR reading image {os.path.join(patient_subdirectory, img_name)}\033[0m", flush=True)
            print("\033[31mSkipping image "+patientID+" "+subdirectory+"\033[0m",flush=True)
            eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading image)")
            continue
       except Exception as e:
            print(f"\033[31mERROR:\033[0m {e}", flush=True)
            print("\033[31mSkipping image"+patientID+" "+subdirectory+"\033[0m",flush=True)
            eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading image)")
            continue
       
       if msk_name != '':
           try:
               #Load mask image
               msk = nib.load(os.path.join(patient_subdirectory,msk_name))
               msk_data = msk.get_fdata()
               img_data_masked = img_data[msk_data > 0]
           except FileNotFoundError:
                print(f"\033[31mERROR reading mask {os.path.join(patient_subdirectory, msk_name)}\033[0m", flush=True)
                print("\033[31mSkipping mask"+patientID+" "+subdirectory+"\033[0m",flush=True)
                eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading mask)")
                continue
           except Exception as e:
                print(f"\033[31mERROR:\033[0m {e}", flush=True)
                print("\033[31mSkipping mask"+patientID+" "+subdirectory+"\033[0m",flush=True)
                eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading mask)")
                continue
       else:
           img_data_masked=img_data
        
        
       bin_edges=np.array([]) 
       r_img_data = np.copy(img_data)

       try:
           if method.lower() == 'binning_number':
               min_value = img_data_masked.min()
               max_value = img_data_masked.max()
               bin_edges = np.linspace(min_value, max_value, int(n_bins) + 1)
               r_img_data = np.digitize(img_data, bin_edges) - 1
               r_img_data = np.clip(r_img_data, 0, int(n_bins) - 1)

           elif method.lower() == 'binning_number_v2':
               min_value = img_data_masked.min()
               max_value = img_data_masked.max()
               r_img_data = ((img_data - min_value)/(max_value - min_value))*255
               r_img_data = r_img_data.astype(np.uint8)
               
           elif method.lower() == 'binning_width':
               min_value, max_value = img_data_masked.min(), img_data_masked.max()
               bin_edges = np.arange(min_value, max_value + bin_width, bin_width)
               r_img_data = np.digitize(img_data_masked, bin_edges) - 1
               min_value = img_data_masked.min()
               max_value = img_data_masked.max()
               bin_edges = np.arange(min_value, max_value + bin_width, bin_width)
               r_img_data = np.digitize(img_data, bin_edges) - 1
               r_img_data = np.clip(r_img_data, 0, len(bin_edges) - 2)

           elif method.lower() == 'linear_scaling':
                min_value = img_data_masked.min()
                max_value = img_data_masked.max()
                r_img_data = ((img_data - min_value) / (max_value - min_value)) * (scale_max - scale_min) + scale_min


           elif method.lower() == 'zscore_normalization':
               mean = img_data_masked.mean()
               std_dev = img_data_masked.std()
               r_img_data = (img_data - mean) / std_dev 

           elif method.lower() == 'robust_scaling':
                median = np.median(img_data_masked)
                p1 = np.percentile(img_data_masked, lower_bound)
                p2 = np.percentile(img_data_masked, upper_bound)
                r_img_data = (img_data - median) / (p2 - p1)

           else:
                print(f"\033[31mERROR: Method '{method}' is not recognized\033[0m", flush=True)
                sys.exit(2)

       except Exception as e:
            print(f"\033[31mERROR computing intensity resampling with method '{method}' for image '{os.path.join(patient_subdirectory, img_name)}':\033[0m {e}", flush=True)
            print("\033[31mSkipping"+patientID+" "+subdirectory+"\033[0m",flush=True)
            eprint("Skipping "+patientID+" "+subdirectory+" (ERROR computing intensity resampling)")
            continue            
       try:
            # Create a new NIfTI image with the modified data
            r_img=nib.Nifti1Image(r_img_data,affine=img.affine,header=img.header)
            nib.save(r_img,os.path.join(outpath,patientID,subdirectory,r_img_name))
            if verbose:
                hprint("Resampled image saved ",os.path.join(patient_subdirectory, r_img_name))
       except Exception as e:
            print(f"\033[31mERROR writing {os.path.join(patient_subdirectory, r_img_name)}:\033[0m {e}", flush=True)           

def ordinal_suffix(n):
    if 11 <= n % 100 <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix


if __name__ == "__main__":
    main(sys.argv[1:])   
