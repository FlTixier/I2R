#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

The `N4-BIAS-FIELD-CORRECTION` module corrects images for bias field inhomogeneities, which are often present in MRI images. This module allows users to specify target areas for correction using masks and can output the estimated bias field as a separate image.

Options
-------

The `N4-BIAS-FIELD-CORRECTION` module supports the following options:

- **verbose**: Enable verbose mode for detailed process information (default: False).
- **timer**: Enable a timer to record execution time (default: False).
- **inputFolder**: Path to the folder containing the input images.
- **outputFolder**: Path to save the corrected images.
- **outputFolderSuffix**: Adds a suffix to the `inputFolder` name to create the output folder.
- **log**: Path to a log file for saving detailed output information.
- **new_log_file**: Create a new log file, overwriting any existing file with the same name.
- **skip**: Path to a file listing subfolders in `inputFolder` to exclude from processing.
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **image_filename**: Name of the image file to read for bias correction.
- **mask_filename**: Name of the mask file to apply correction only within a specified area (optional).
- **corrected_image_filename**: Name for the corrected output image (default: img_n4biasCorr.nii.gz).
- **bias_field_image_filename**: Specify an output name for saving the estimated bias field image (optional).
- **suffix_name**: Suffix to add to the corrected image name, overriding `corrected_image_filename` if specified.

Example Usage
-------------

The following example demonstrates how to use the `N4-BIAS-FIELD-CORRECTION` module:

.. code-block:: bash

    N4-BIAS-FIELD-CORRECTION:
    {
        inputFolder: /path/to/NIFTI_folder
        image_filename: img.nii.gz
        mask_filename: msk.nii.gz  # Optional: apply correction only within mask
        corrected_image_filename: img_n4biasCorr.nii.gz
        bias_field_image_filename: field.nii.gz  # Optional: output for estimated bias field
        log: /path/to/logs/bias_field_correction.log
        new_log: True  # Create a new log file or append to an existing one
    }

In this example:

- **inputFolder**: Specifies the folder containing images for bias correction.
- **image_filename** and **corrected_image_filename**: Define input and output filenames.
- **bias_field_image_filename**: Saves the estimated bias field image.
- **log**: Specifies the path for the log file.
"""


# NiftiN4BiasFieldCorrection_multiprocessing performs N4 bias field correction on NIfTI images,
# targeting bias field inhomogeneities primarily in MRI data.
#
# Usage:
#     NiftiN4BiasFieldCorrection_multiprocessing.py -i <inputFolder> -o <outputFolder> [options]
# 
# Options:
#   -h, --help                       Show this help message and exit
#   -v, --verbose                    Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>  Input folder containing NIfTI images
#   -o, --outputFolder <outputFolder> Output folder to save corrected images
#       --img_name <image name>      Name of the input image (default: img.nii.gz)
#       --msk_name <mask name>       Name of the mask file to limit correction area (optional)
#       --corrected_img_name <output name> Name for saving the corrected image (default: corrected_img.nii.gz)
#       --bias_field_name <field image name> Name for saving the bias field image (optional)
#   -e <suffix>                      Suffix to append to output image names (default: "")
#   -S <skip file path>              Path to a file listing filenames to skip
#       --include <include file path> Path to a file listing filenames to include (default: include all)
#       --log <log file path>        Redirect stdout to a log file
#       --new_log                    Overwrite the previous log file if it exists
#   -j, --n_jobs <number of jobs>    Number of simultaneous jobs (default: 1)
#
# Help:
#     NiftiN4BiasFieldCorrection_multiprocessing.py -h

import sys, getopt, os
from tqdm import tqdm
import SimpleITK as sitk
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
    verbose = False
    img = 'img.nii.gz'
    msk = ''
    corrected_img = 'corrected_img.nii.gz'
    bias_field_name = ''
    suffix = ''
    n_jobs = 1
    skip_file_name = ''
    skip_files = []
    include_file_name = ''
    include_files = []
    log = ''
    new_log = False

    try:
        opts, args = getopt.getopt(argv, "h:vi:o:j:S:e:", ["log=", "new_log", "n_jobs=", "verbose", "help", "inputFolder=", "outputFolder=", "img_name=", "msk_name=", "corrected_img_name=", "bias_field_name=", "skip=", "include="])
    except getopt.GetoptError as err:
        print(f'Error: {err.msg}')
        print('Usage: NiftiN4BiasFieldCorrection_multiprocessing.py [-h|--help] [-v|--verbose] [-i|--inputFolder <inputfolder>] [-o|--outputFolder <outfolder>] [--img_name <image name>] [--msk_name <mask name>] [--corrected_img_name <corrected image name>] [--bias_field_name <bias field image name>] [-e <suffix>] [--skip <skip file path>] [--include <include file path>] [--log <log file path>] [-j|--n_jobs <number of simultaneous jobs>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tNiftiN4BiasFieldCorrection_multiprocessing.py\n")
            print("SYNOPSIS")
            print("\tNiftiN4BiasFieldCorrection_multiprocessing.py [-h|--help] [-v|--verbose] [-i|--inputFolder <inputfolder>] "
                  "[-o|--outputFolder <outfolder>] [--img_name <image name>] [--msk_name <mask name>] "
                  "[--corrected_img_name <corrected image name>] [-e <suffix>] [--skip <skip file path>] "
                  "[--include <include file path>] [--log <log file path>] [-j|--n_jobs <number of simultaneous jobs>]\n")
            print("DESCRIPTION")
            print("\tPerform N4 bias field correction on NIfTI images.\n")
            print("OPTIONS")
            print("\t -h, --help: Show this help message and exit")
            print("\t -v, --verbose: Enable verbose output (default: False)")
            print("\t -i, --inputFolder: Input folder containing NIfTI images")
            print("\t -o, --outputFolder: Output folder to save corrected images")
            print("\t --img_name: Name of the input image (default: img.nii.gz)")
            print("\t --msk_name: Name of the input mask (default: '')")
            print("\t --corrected_img_name: Name for the corrected image (default: corrected_img.nii.gz)")
            print("\t --bias_field_name: Name for the bias field image (default: bias_field.nii.gz)")
            print("\t -e: Suffix to append to output image names (default: \"\")")
            print("\t -S, --skip: Path to a file listing filenames to skip")
            print("\t --include: Path to a file listing filenames to include (default: include all)")
            print("\t --log: Redirect stdout to a log file")
            print("\t --new_log: Overwrite the previous log file")
            print("\t -j, --n_jobs: Number of simultaneous jobs (default: 1)")
            sys.exit(0)
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-j", "--n_jobs"):
            n_jobs = int(arg)
        elif opt in ("--skip"):
            skip_file_name = arg
        elif opt in ("--include"):
            include_file_name = arg
        elif opt in ("--log"):
            log = arg
        elif opt in ("--new_log"):
            new_log = True
        elif opt in ("--img_name"):
            img = arg
        elif opt in ("--msk_name"):
            msk = arg
        elif opt in ("--corrected_img_name"):
            corrected_img = arg
        elif opt in ("--bias_field_name"):
            bias_field_name = arg
        elif opt in ("-e"):
            suffix = arg

    if log != '':
        if new_log:
            f = open(log, 'w+')
        else:
            f = open(log, 'a+')
        sys.stdout = f

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
            print("\033[33mWARNING! Input and output paths are identical, corrected images will be saved in the input folder\033[0m", flush=True)

    if inpath == '':
        print("\033[31mERROR! No input folder specified\033[0m", flush=True)
        sys.exit(1)

    if verbose:
        msg = (
            f"Input path: {inpath}\n"
            f"Output path: {outpath}\n"
            f"Image to process: {img}\n"
            f"Mask: {msk}\n"
            f"Corrected image name: {corrected_img}\n"
            f"Bias field image name: {bias_field_name}\n"
            f"Output suffix name: {suffix}\n"
            f"n_jobs: {n_jobs}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files, 5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files, 5)}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose: {verbose}\n"
        )

        hprint_msg_box(msg=msg, indent=2, title=f"N4_BIAS_FIELD_CORRECTION {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if n_jobs == 1:
        for patient in tqdm(glob.glob(inpath + "/*"),
                            ncols=100,
                            desc="N4 Bias Field Correction",
                            bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                            colour="yellow"):
            correct_bias_field(patient, inpath, outpath, img, msk, corrected_img, bias_field_name, suffix, skip_files, include_files, verbose, log)
    else:
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(correct_bias_field,
                              [(patient, inpath, outpath, img, msk, corrected_img, bias_field_name, suffix, skip_files, include_files, verbose, log) for patient in glob.glob(inpath + "/*")]),
                 ncols=100,
                 desc="N4 Bias Field Correction",
                 bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                 colour="yellow")

def correct_bias_field(patient, inpath, outpath, img_name, msk_name, corrected_img_name, bias_field_name, suffix, skip_files, include_files, verbose, log):
    patientID = os.path.basename(patient)

    if len(include_files) > 0 and patientID not in include_files:
        if verbose:
            print(f"\n{patientID} ({patient}) is not in the list of patients to include", flush=True)
        return

    if len(skip_files) > 0 and patientID in skip_files:
        if verbose:
            print(f"\nSkipping {patientID} ({patient})", flush=True)
        return

    if verbose:
        hprint(f"Processing {patientID}", patient)

    if not os.path.exists(os.path.join(outpath, patientID)):
        os.makedirs(os.path.join(outpath, patientID))
   
    for patient_subdirectory in glob.glob(patient+"/*"):
       subdirectory=os.path.basename(patient_subdirectory)
       if verbose:
           print(f"{patientID}: {subdirectory}", flush=True)
       
       if not os.path.exists(os.path.join(outpath,patientID,subdirectory)):
           os.makedirs(os.path.join(outpath,patientID,subdirectory))
       
       try: 
           img = sitk.ReadImage(os.path.join(patient_subdirectory, img_name))
       except FileNotFoundError:
            print(f"\033[31mERROR reading image {os.path.join(patient, img_name)}\033[0m", flush=True)
            eprint(f"Skipping {patientID} (ERROR reading image)")
            continue
       except Exception as e:
           print(f"\033[31mERROR:\033[0m {e}", flush=True)
           print("\033[31mSkipping image"+patientID+" "+subdirectory+"\033[0m",flush=True)
           eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading image)")
           continue
    
       mask = None
       if msk_name != '':
           try:
               mask = sitk.ReadImage(os.path.join(patient_subdirectory, msk_name))
           except FileNotFoundError:
               print(f"\033[31mERROR reading mask {os.path.join(patient, msk_name)}\033[0m", flush=True)
               eprint(f"Skipping {patientID} (ERROR reading mask)")
               continue
           except Exception as e:
               print(f"\033[31mERROR:\033[0m {e}", flush=True)
               print("\033[31mSkipping image"+patientID+" "+subdirectory+"\033[0m",flush=True)
               eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading mask)")
               continue
       try:
           # Perform check and cast the image if needed
           pixel_type = img.GetPixelIDTypeAsString() 
           if pixel_type != "32-bit float" and pixel_type != "64-bit float":
               print(f"\033[33mWARNING! Casting image to 32-bit float. SimpleITK does not support {pixel_type} for 3D bias field correction\033[0m",flush=True)
               img = sitk.Cast(img, sitk.sitkFloat32)
           # Check and cast the mask to an appropriate type
           mask_pixel_type = mask.GetPixelIDTypeAsString()
           if mask_pixel_type not in ["8-bit unsigned integer", "16-bit unsigned integer"]:
               print(f"\033[33mWARNING! Casting mask to 8-bit unsigned integer. SimpleITK does not support {mask_pixel_type} for masks in 3D bias field correction\033[0m", flush=True)
               mask = sitk.Cast(mask, sitk.sitkUInt8)
            
           corrector = sitk.N4BiasFieldCorrectionImageFilter()
           if mask:
               corrected_img = corrector.Execute(img, mask)
           else:
               corrected_img = corrector.Execute(img)
           if bias_field_name != '':
               bias_field = corrector.GetLogBiasFieldAsImage(img)
               sitk.WriteImage(bias_field, os.path.join(outpath, patientID,subdirectory, bias_field_name))
               if verbose:
                    print(f"Saved bias field image to {os.path.join(outpath, patientID, bias_field_name)}", flush=True)
                
           if suffix:
               corrected_img_name = os.path.splitext(os.path.splitext(img_name)[0])[0] + "_" + suffix + ".nii.gz"
    
           sitk.WriteImage(corrected_img, os.path.join(outpath, patientID,subdirectory, corrected_img_name))
           if verbose:
               print(f"Saved corrected image to {os.path.join(outpath, patientID, corrected_img_name)}", flush=True)
       except Exception as e:
           print(f"\033[31mERROR during N4 bias field correction: {e}\033[0m", flush=True)
           eprint(f"Skipping {patientID} (ERROR during correction)")

if __name__ == "__main__":
    main(sys.argv[1:])
