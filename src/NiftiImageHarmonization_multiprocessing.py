#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `I-HARMONIZE` module allows users to harmonize images to a reference image using various harmonization methods (currently, only histogram matching is available). Harmonization can be applied to the entire image or limited to specific areas using masks.

Options
-------

The `I-HARMONIZE` module supports the following options:

- **verbose**: Enable verbose output for detailed process information (default: False).
- **timer**: Enable a timer to record execution time (default: False).
- **inputFolder**: Path to the folder containing the input images.
- **outputFolder**: Path to save the harmonized images.
- **outputFolderSuffix**: Adds a suffix to the `inputFolder` name to create the output folder.
- **log**: Path to a log file for saving detailed output information.
- **new_log_file**: Create a new log file, overwriting any existing file with the same name.
- **skip**: Path to a file listing subfolders in `inputFolder` to exclude from processing.
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **image_filename**: Name of the image file to read for harmonization.
- **mask_filename**: Name of the mask file for the input image, to restrict harmonization to specific regions (optional).
- **reference_image**: Full path to the reference image for harmonization.
- **reference_mask**: Full path to the mask file for the reference image, for region-specific harmonization (optional).
- **harmonized_image_filename**: Name for the harmonized output image (default: h_img.nii.gz).
- **method**: Harmonization method to apply (currently, only "histogram_matching" is available).
- **suffix_name**: Suffix to add to the output image name, overriding `harmonized_image_filename` if specified.

Example Usage
-------------

The following example demonstrates how to use the `I-HARMONIZE` module:

.. code-block:: bash

    I-HARMONIZATION:
    {
        inputFolder: /path/to/NIFTI_folder
        image_filename: img.nii.gz
        mask_filename: msk.nii.gz
        harmonized_image_filename: img_h.nii.gz
        reference_image: /path/to/Reference/Images/img.nii.gz
        reference_mask: /path/to/Reference/Images/msk.nii.gz
        method: histogram_matching
        log: /path/to/logs/harmonize.log
        new_log: True
    }

In this example:

- **inputFolder**: Specifies the folder containing the images to harmonize.
- **image_filename** and **harmonized_image_filename**: Define the input and output filenames.
- **reference_image**: Specifies the reference image used for harmonization.
- **method**: Indicates "histogram_matching" as the harmonization method.
- **log**: Specifies the path for the log file.
"""

# NiftiHarmonization_multiprocessing harmonizes NIfTI images to a reference image using various methods,
# currently supporting histogram matching. Future updates will include additional harmonization methods.
#
# Usage:
#     NiftiHarmonization_multiprocessing.py -i <inputFolder> -o <outputFolder> [options]
# 
# Options:
#   -h, --help                       Show this help message and exit
#   -v, --verbose                    Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>  Input folder containing NIfTI images
#   -o, --outputFolder <outputFolder> Output folder to save harmonized images
#       --img_name <image name>      Name of the input image (default: img.nii.gz)
#       --msk_name <mask name>       Name of the input mask (optional, default: '')
#       --ref_img <reference image path> Full path to the reference image for harmonization
#       --ref_msk <reference mask path> Full path to the reference mask for harmonization (optional)
#       --harmonized_img_name <output name> Name for the harmonized image (default: h_img.nii.gz)
#       --method <harmonization method> Harmonization method to apply (default: histogram_matching)
#       --n_bins <number of bins>    Number of bins (used for histogram matching, default: 256)
#       --n_matchPoints <control points> Number of control points for cumulative distribution matching (default: 10)
#   -e <suffix>                      Suffix to append to output image names (overrides harmonized_img_name)
#   -S <skip file path>              Path to a file listing filenames to skip
#       --include <include file path> Path to a file listing filenames to include (default: include all)
#       --log <log file path>        Redirect stdout to a log file
#       --new_log                    Overwrite an existing log file if it exists
#   -j, --n_jobs <number of jobs>    Number of simultaneous jobs (default: 1)
#
# Help:
#     NiftiHarmonization_multiprocessing.py -h
#

import sys, getopt, os
from tqdm import tqdm
import SimpleITK as sitk
import numpy as np
import glob
import multiprocessing
from datetime import datetime
from utils import hprint
from utils import eprint
from utils import hprint_msg_box
from utils import format_list_multiline

def main(argv):
    inpath = ''
    outpath = ''
    dif_path = False
    verbose = False
    img = 'img.nii.gz'
    msk = ''
    ref_img = '' #full path with referernce image for harmonization
    ref_msk = '' #full path with referernce mask for harmonization
    h_img = 'h_img.nii.gz'
    suffix = ''
    n_bins = 256
    n_matchPoints = 10
    method = 'histogram_matching'  # Default harmonization method
    n_jobs = 1
    skip_file_name = ''
    skip_files = []
    include_file_name = ''
    include_files = []
    log = ''
    new_log = False
    
    try:
        opts, args = getopt.getopt(argv, "h:vi:o:r:j:S:e:", ["log=","new_log", "n_jobs=", "verbose", "help", "inputFolder=", "outputFolder=", "img_name=", "msk_name=" ,"ref_img=", "ref_msk=", "harmonized_img_name=", "method=", "n_bins=","n_matchPoints=", "skip=", "include="])
    except getopt.GetoptError as err:
        print(f'Error: {err.msg}')
        print('Usage: NiftiImageHarmonization_multiprocessing.py [-h|--help] [-v|--verbose] [-i|--inputFolder <inputfolder>] [-o|--outputFolder <outfolder>] [--img_name <image name>] [--ref_img_name <reference image name>] [--resampled_img_name <resampled image name>] [-e <suffix>] [--method <harmonization method>] [--n_bins <number of bins>] [--skip <skip file path>] [--include <include file path>] [--log <log file path>] [-j|--n_jobs <number of simultaneous jobs>]')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            if opt in ("-h", "--help"):
                print("NAME")
                print("\tNiftiHarmonization_multiprocessing.py\n")
                print("SYNOPSIS")
                print("\tNiftiHarmonization_multiprocessing.py [-h|--help] [-v|--verbose] [-i|--inputFolder <inputfolder>] "
                      "[-o|--outputFolder <outfolder>] [--img_name <image name>] [--ref_img <reference image path>] "
                      "[--harmonized_img_name <harmonized image name>] [-e <suffix>] [--method <harmonization method>] "
                      "[--n_bins <number of bins>] [--skip <skip file path>] [--include <include file path>] "
                      "[--log <log file path>] [-j|--n_jobs <number of simultaneous jobs>]\n")
                print("DESCRIPTION")
                print("\tHarmonize voxel intensity of NIfTI images using specified methods such as histogram matching.\n")
                print("OPTIONS")
                print("\t -h, --help: Show this help message and exit")
                print("\t -v, --verbose: Enable verbose output (default: False)")
                print("\t -i, --inputFolder: Input folder containing NIfTI images")
                print("\t -o, --outputFolder: Output folder to save harmonized images")
                print("\t --img_name: Name of the input image (default: img.nii.gz)")
                print("\t --msk_name: Name of the input mask")
                print("\t --ref_img: Full path to the reference image for harmonization")
                print("\t --ref_msk: Full path to the reference mask for harmonization")
                print("\t --harmonized_img_name: Name for the harmonized image (default: h_img.nii.gz)")
                print("\t -e: Suffix to append to output image names (default: \"\")")
                print("\t --method: Image harmonization method to apply (default: histogram_matching)")
                print("\t --n_bins: Number of bins (used for histogram matching)")
                print("\t --n_matchPoints: Number of control points used to match the cummulative distribution functions (used for histogram matching)")
                print("\t -S, --skip: Path to a file listing filenames to skip")
                print("\t --include: Path to a file listing filenames to include (default: include all)")
                print("\t --log: Redirect stdout to a log file")
                print("\t --new_log: Overwrite the previous log file")
                print("\t -j, --n_jobs: Number of simultaneous jobs (default: 1)")
                sys.exit(0)
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--n_bins"):
            n_bins = int(arg)
        elif opt in ("--n_matchPoints"):
            n_matchPoints = int(arg)
        elif opt in ("-j", "--n_jobs"):
            n_jobs = int(arg)
        elif opt in ("--skip"):
            skip_file_name = arg
        elif opt in ("--include"):
            include_file_name = arg
        elif opt in ("--log"):
            log = arg
        elif opt in ("--new_log"):
            new_log= True
        elif opt in ("--img_name"):
            img = arg
        elif opt in ("--msk_name"):
            msk = arg
        elif opt in ("--ref_img"):
            ref_img = arg
        elif opt in ("--ref_msk"):
            ref_msk = arg
        elif opt in ("--harmonized_img_name"):
            h_img = arg
        elif opt in ("-e"):
            suffix = arg
        elif opt in ("--method"):
            method = arg
    
    if log != '':
        if new_log:
            f = open(log,'w+')
        else:
            f = open(log,'a+')
        sys.stdout = f   
    
    if msk == '' and ref_msk == '':
        if verbose:
            print("\033[33mWARNING! No mask was provided; harmonization will be performed on the entire image.\033[0m", flush=True)
    if msk == '' and not ref_msk == '':
        if verbose:
            print("\033[33mWARNING! A mask was provided for the reference image but not for the images to be harmonized\033[0m", flush=True)       
    if not msk == '' and ref_msk == '':
        if verbose:
            print("\033[33mWARNING! A mask was provided for the images to harmonize but not for the reference image\033[0m", flush=True)       
            
    if skip_file_name != '':
        try:
            with open(skip_file_name, 'r') as file:
                skip_files = file.read().splitlines()
        except:
            print("\033[31mERROR! Unable to read the skip file\033[0m", flush=True)
    
    if include_file_name != '':
        try:
            with open(include_file_name, 'r') as file:
                include_files = file.read().splitlines()
        except:
            print("\033[31mERROR! Unable to read the include file\033[0m", flush=True)
    
    if outpath == '':
        outpath = inpath
        if verbose:
            print("\033[33mWARNING! No output folder specified, results will be saved in the input folder\033[0m", flush=True)
    elif outpath == inpath:
        if verbose:
            print("\033[33mWARNING! Input and output paths are identical, resampled images will be saved in the input folder\033[0m", flush=True)
    else:
        dif_path = True
    
    if inpath == '':
        print("\033[31mERROR! No input folder specified\033[0m", flush=True)
        sys.exit(1)
    
    if ref_img == '':
        print("\033[31mERROR! A reference image is required!\033[0m",flush=True)
        sys.exit(1)
    
    if suffix != '':
        h_img = os.path.splitext(os.path.splitext(os.path.basename(img))[0])[0] + "_" + suffix + ".nii.gz"

    if verbose:
        msg = (
            f"Input path: {inpath}\n"
            f"Output path: {outpath}\n"
            f"Image to process: {img}\n"
            f"Process voxels in mask: {msk}\n"
            f"Harmonize image name: {h_img}\n"
            f"Output suffix name: {suffix}\n"
            f"Full path to the reference image: {ref_img}\n"
            f"Full path to the reference mask: {ref_msk}\n"
            f"Method: {method}\n"
            f"Number of bins: {n_bins}\n"
            f"Number of match points: {n_matchPoints}\n"
            f"n_jobs: {n_jobs}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose: {verbose}\n"  
            )
        
        hprint_msg_box(msg=msg, indent=2, title=f"I-HARMONIZE {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")    



    if n_jobs == 1:
        for patient in tqdm(glob.glob(inpath + "/*"),
                            ncols=100,
                            desc="Image Harmonization",
                            bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                            colour="yellow"):
            harmonize_image(patient, inpath, outpath, img, msk, ref_img, ref_msk, h_img, method, n_bins, n_matchPoints, dif_path, skip_files, include_files, verbose, log)
    else:
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(harmonize_image,
                              [(patient, inpath, outpath, img, msk, ref_img, ref_msk, h_img, method, n_bins, n_matchPoints, dif_path, skip_files, include_files, verbose, log) for patient in glob.glob(inpath + "/*")]),
                 ncols=100,
                 desc="Image Harmonization",
                 bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                 colour="yellow")


def harmonize_image(patient, inpath, outpath, img_name, msk_name, ref_img_name, ref_msk_name, h_img_name, method, n_bins, n_matchPoints, dif_path, skip_files, include_files, verbose, log):

    patientID = os.path.basename(patient)
    
    if len(include_files) > 0:
        if patientID not in include_files:
            if verbose:
                print(f"\n{patientID} ({patient}) is not in the list of patients to include", flush=True)
            return

    if len(skip_files) > 0:
        if patientID in skip_files:
            if verbose:
                print(f"\nSkipping {patientID} ({patient})", flush=True)
            return

    if verbose:
        hprint(f"processing {patientID}",patient)

    if not os.path.exists(os.path.join(outpath, patientID)):
        os.makedirs(os.path.join(outpath, patientID))

    try:
        ref_img=sitk.ReadImage(ref_img_name)
    except FileNotFoundError:
        print(f"\033[31mERROR reading image {ref_img_name}\033[0m", flush=True)
        sys.exit(1)    
    
    ref_msk = None
    if ref_msk_name != '':
        try:
            ref_msk = sitk.ReadImage(ref_msk_name)
        except FileNotFoundError:
            print(f"\033[31mERROR reading image {ref_msk_name}\033[0m", flush=True)
            return 

    for patient_subdirectory in glob.glob(patient + "/*"):
        subdirectory = os.path.basename(patient_subdirectory)
        if verbose:
            print(f"{patientID}: {subdirectory}", flush=True)

        if not os.path.exists(os.path.join(outpath, patientID, subdirectory)):
            os.makedirs(os.path.join(outpath, patientID, subdirectory))

        try:
            # Load the input and reference NIfTI images
            img = sitk.ReadImage(os.path.join(patient_subdirectory, img_name))
        except FileNotFoundError:
            print(f"\033[31mERROR reading image {os.path.join(patient_subdirectory, img_name)}\033[0m", flush=True)
            print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
            eprint(f"Skipping {patientID} {subdirectory} (ERROR reading image)")
            continue
        except Exception as e:
            print(f"\033[31mERROR:\033[0m {e}", flush=True)
            print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
            eprint(f"Skipping {patientID} {subdirectory} (ERROR reading image)")
            continue
        
        msk = None
        if msk_name != '':
            try:
                msk = sitk.ReadImage(os.path.join(patient_subdirectory, msk_name))
            except FileNotFoundError:
                print(f"\033[31mERROR reading mask {os.path.join(patient_subdirectory, msk_name)}\033[0m", flush=True)
                print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                eprint(f"Skipping {patientID} {subdirectory} (ERROR reading mask)")
                continue
            except Exception as e:
                print(f"\033[31mERROR:\033[0m {e}", flush=True)
                print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                eprint(f"Skipping {patientID} {subdirectory} (ERROR reading mask)")
                continue

        # Call the selected harmonization method
        try:
            if method == 'histogram_matching':
                matcher = sitk.HistogramMatchingImageFilter()
                matcher.SetNumberOfHistogramLevels(n_bins)
                matcher.SetNumberOfMatchPoints(n_matchPoints)
                
                if msk and ref_msk:  # If both masks are provided, use them
                    if verbose:
                        print(f"Harmonize {patientID} {subdirectory} with masks",flush=True)   
                    
                    msk_array = sitk.GetArrayFromImage(msk) > 0
                    
                    # Convert images and masks to numpy arrays
                    img_array = sitk.GetArrayFromImage(img)
                    ref_img_array = sitk.GetArrayFromImage(ref_img)
                    ref_msk_array = sitk.GetArrayFromImage(ref_msk) > 0
    
                    # Extract intensity values from the reference image using the reference mask
                    ref_masked_values = ref_img_array[ref_msk_array]
    
                    # Create a temporary SimpleITK image from these values
                    # Reshape to match the original image size but only populate masked areas
                    temp_ref_img_array = np.zeros_like(ref_img_array)
                    temp_ref_img_array[ref_msk_array] = ref_masked_values
    
                    # Convert the temporary array back to a SimpleITK image
                    temp_ref_img = sitk.GetImageFromArray(temp_ref_img_array)
                    temp_ref_img.CopyInformation(ref_img)
    
                    # Mask the input image as well
                    temp_img_array = np.zeros_like(img_array)
                    temp_img_array[msk_array] = img_array[msk_array]
                    temp_img = sitk.GetImageFromArray(temp_img_array)
                    temp_img.CopyInformation(img)
    
                    # Perform histogram matching using the masked images
                    matched_image = matcher.Execute(temp_img, temp_ref_img)
    
                    # Convert the matched image to a numpy array
                    matched_array = sitk.GetArrayFromImage(matched_image)
    
                    # Update only the masked region in the input image
                    img_array[msk_array] = matched_array[msk_array]
    
                    # Convert back to SimpleITK image
                    matched_image = sitk.GetImageFromArray(img_array)
                    matched_image.CopyInformation(img)
                    
                    
                elif msk and not ref_msk:  # If masks are provided for images to harmonize only (NOT RECOMMENDED)
                    if verbose:
                        print(f"\033[33mHarmonize {patientID} {subdirectory} with mask for input image only (NOT RECOMMENDED)\033[0m",flush=True)       
                    msk_array = sitk.GetArrayFromImage(msk) > 0
                    
                    # Convert images to numpy arrays
                    img_array = sitk.GetArrayFromImage(img)
                    ref_img_array = sitk.GetArrayFromImage(ref_img)
    
    
                    # Mask the input image as well
                    temp_img_array = np.zeros_like(img_array)
                    temp_img_array[msk_array] = img_array[msk_array]
                    temp_img = sitk.GetImageFromArray(temp_img_array)
                    temp_img.CopyInformation(img)
    
                    # Perform histogram matching using the masked images
                    matched_image = matcher.Execute(temp_img, ref_img)
    
                    # Convert the matched image to a numpy array
                    matched_array = sitk.GetArrayFromImage(matched_image)
    
                    # Update only the masked region in the input image
                    img_array[msk_array] = matched_array[msk_array]
    
                    # Convert back to SimpleITK image
                    matched_image = sitk.GetImageFromArray(img_array)
                    matched_image.CopyInformation(img)
                    
                elif not msk and ref_msk:  # If mask is provided for reference image only (NOT RECOMMENDED)
                    if verbose:
                        print(f"\033[33mHarmonize {patientID} {subdirectory} with mask for reference image only (NOT RECOMMENDED)\033[0m", flush=True)   
                    
                    # Convert image and mask to numpy arrays
                    ref_img_array = sitk.GetArrayFromImage(ref_img)
                    ref_msk_array = sitk.GetArrayFromImage(ref_msk) > 0
    
                    # Extract intensity values from the reference image using the reference mask
                    ref_masked_values = ref_img_array[ref_msk_array]
    
                    # Create a temporary SimpleITK image from these values
                    # Reshape to match the original image size but only populate masked areas
                    temp_ref_img_array = np.zeros_like(ref_img_array)
                    temp_ref_img_array[ref_msk_array] = ref_masked_values
    
                    # Convert the temporary array back to a SimpleITK image
                    temp_ref_img = sitk.GetImageFromArray(temp_ref_img_array)
                    temp_ref_img.CopyInformation(ref_img)
    
                    # Perform histogram matching using the masked images
                    matched_image = matcher.Execute(img, temp_ref_img)
    
                else: #perform harmonization on the full image
                    if verbose:
                        print(f"Harmonize {patientID} {subdirectory}",flush=True)   
                    matched_image = matcher.Execute(img, ref_img)
            else:
                print(f"\033[31mERROR: Method '{method}' is not recognized\033[0m", flush=True)
                continue
        except Exception as e:
            print(f"\033[31mERROR computing harmonization using method '{method}' for image '{os.path.join(patient_subdirectory, img_name)}':\033[0m {e}", flush=True)
            continue

        try:
            # Create a new NIfTI image with the harmonized data
            sitk.WriteImage(matched_image, os.path.join(outpath, patientID, subdirectory, h_img_name))
            if verbose:
                print(f"Saved harmonized image to {os.path.join(patient_subdirectory, h_img_name)}", flush=True)
        except Exception as e:
            print(f"\033[31mERROR writing {os.path.join(patient_subdirectory, h_img_name)}:\033[0m {e}", flush=True)

if __name__ == "__main__":
    main(sys.argv[1:])  
