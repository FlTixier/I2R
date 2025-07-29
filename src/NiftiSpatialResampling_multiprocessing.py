#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `SPATIAL_RESAMPLING` module resamples NIfTI images to a specified resolution, providing options for interpolation and voxel size. It uses the Convert3D (c3d) program from ITK-SNAP (http://www.itksnap.org) or SimpleITK for spatial transformations, depending on configuration.

Options
-------

The `SPATIAL_RESAMPLING` module accepts the following options:

- **verbose**: Enable verbose output for more detailed process information (default: False).
- **timer**: Enable a timer to measure execution time (default: False).
- **inputFolder**: Path to the folder containing input NIfTI files.
- **outputFolder**: Path to save the resampled output files.
- **outputFolderSuffix**: Adds a suffix to the `inputFolder` name to create an output folder.
- **with-segmentation**: Specify if folders contain segmentation files.
- **all-data-with-segmentation**: Specify if all folders contain segmentation files (default: True).
- **log**: Path to a log file for saving detailed information about the resampling process.
- **new_log_file**: Create a new log file; if a file with the same name exists, it will be overwritten.
- **skip**: Path to a file listing subfolders to exclude from resampling.
- **include**: Path to a file listing subfolders to include in resampling (all subfolders included by default).
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **image_interpolation**: Interpolation method for images. Options: `NearestNeighbor`, `Linear`, `Cubic`, `Sinc`, `Gaussian`, `B-Spline` (default: Linear).
- **mask_interpolation**: Interpolation method for masks/segmentation files. Options: `NearestNeighbor`, `Linear`, `Cubic`, `Sinc`, `Gaussian`, `B-Spline` (default: NearestNeighbor).
- **use_c3d**: Use the c3d program for resampling instead of SimpleITK.
- **voxel_size**: Specify the x, y, and z dimensions of the voxels in mm³. Only isotropic resampling is supported (default: 1).
- **suffix_name**: Add a suffix to resampled image and segmentation files (default: "111").

Example Usage
-------------

The following example demonstrates how to use the `SPATIAL_RESAMPLING` module to resample a folder of NIfTI files to 1mm³ isotropic voxel size:

.. code-block:: bash

    SPATIAL_RESAMPLING:
    {
        inputFolder: /path/to/NIFTI_folder
        outputFolderSuffix: 111
        voxel_size: 1  # 1mm³
        image_interpolation: Linear
        mask_interpolation: NearestNeighbor
        suffix_name: 111
        log: /path/to/logs/spatial_resampling.log
    }

In this example:

- **inputFolder**: Specifies the folder containing NIfTI files to be resampled.
- **outputFolderSuffix**: Appends the suffix "111" to the name of `inputFolder` to create the output directory.
- **voxel_size**: Sets the voxel size for resampling to 1mm³.
- **log**: Saves a log file at the specified location, recording details of the resampling process.
"""


# Resample NIfTI images and masks to a specific voxel dimension using SimpleITK or c3d
# C3D (Convert3D) is a part of ITK-SNAP and can be downloaded here: http://www.itksnap.org/pmwiki/pmwiki.php?n=Convert3D.Convert3D
#
# Usage: NiftiResampling_multiprocessing.py -i <inputFolder> -o <outputFolder> [options]
# Options:
#   -v, --verbose                Enable verbose output (default: False)
#       --timer                  Measure execution time (default: False)
#   -i, --inputFolder            Path to the input folder containing NIfTI images
#   -o, --outputFolder           Path to the folder where resampled NIfTI images will be saved
#   -e                           Suffix to add to the name of output images and masks (default: "111")
#   -s, --size                   Size of the resampling voxel in mm³ (default: 1mm)
#   -I, --interpolation          Interpolation method for the image (default: Linear)
#   -M, --mask_interpolation     Interpolation method for masks (default: NearestNeighbor)
#   -j, --n_jobs                 Number of simultaneous jobs (default: 1)
#       --skip                   Path to a file with filenames to skip during processing
#       --include                Path to a file with filenames to include (default: include all)
#       --no-segmentation        Indicate that input folder does not contain segmentation files
#       --all-segmentation       Specify if all folders contain segmentation files (default: False)
#       --log                    Path to a log file for saving output details
#       --new_log                Overwrite an existing log file if it exists
#       --use_c3d                Use c3d program for resampling instead of SimpleITK (default: False)
#
# Help: NiftiResampling_multiprocessing.py -h

import sys, getopt, os
import glob
import subprocess
import shlex
import multiprocessing
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from tqdm import tqdm
from datetime import datetime
from utils import hprint_msg_box
from utils import hprint
from utils import format_list_multiline

def main(argv):
    inpath = ''
    outpath = ''
    verbose = False
    n_jobs=1              #nb of CPUs
    size=1.0              #resampling size in mm
    interpolation = "Linear"
    mask_interpolation = "NearestNeighbor"
    suffix = "111"
    path_to_c3d= "c3d"
    skip_file_name=''
    skip_files=[]
    include_file_name=''
    include_files=[]
    log = ''
    new_log = False
    NoSegmentation = False
    AllSegmentation = False
    use_c3d = False

    
    try:
        opts, args = getopt.getopt(argv, "hvi:o:j:s:I:M:e:S:",["log=","new_log","inputFolder=","outputFolder=","verbose","help","n_jobs=","size=","interpolation=","mask_interpolation=","skip=","include=","no-segmentation","all-segmentation","use_c3d"])
    except getopt.GetoptError:
        print('Usage: NiftiResampling_multiprocessing.py -i <inputFolder> -o <outputFolder> [-v] [-e <suffix>] [-s <size>] [-I <interpolation>] [-M <mask_interpolation>] [-j <numJobs>] [--skip <skipFile>] [--include <includeFile>] [--no-segmentation] [--all-segmentation] [--log <logFile>]')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tNiftiResampling_multiprocessing.py\n")
            print("SYNOPSIS")
            print("\tNiftiResampling_multiprocessing.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>][-o|--outputFolder <outfolder>][-e <suffix name for output imgage and mask>][-s|--size <int>][-I|--interpolation <interpolation method for the image>][-M|--mask_interpolation <interpolation method for the mask>][-j|--n_jobs <number of simultaneous jobs>]\n")
            print("DESRIPTION")
            print("\tResamples NIfTI images and masks to a specific voxel dimension using c3d\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with NIfTI images")
            print("\t -o, --outputFolder: output folder to save resampled NIfTI images")
            print("\t -e: suffix to use in the name for output images and masks (default \"111\")")
            print("\t -s, --size: size of the resampling voxel in mm (default 1mm)")
            print("\t -I, --interpolation: interpolation method for the image (default Linear)")
            print("\t -M, --mask_interpolation: interpolation method for the mask (default NearestNeighbor)")
            print("\t -S, --skip: path to file with filenames to skip when processing resampling")
            print("\t --include: path to file with filenames to include (all files included by default)")
            print("\t, --no-segmentation: input folder does not contain segmentations")
            print("\t, --all-segmentation: input folder contains segmentations for all data (default False)")
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
        elif opt in ("-s", "--size"):
            size= float(arg)
        elif opt in ("-I", "--interpolation"):
             interpolation= arg   
        elif opt in ("-M", "--mask_interpolation"):
            mask_interpolation= arg   
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
        elif opt in ("--no-segmentation"):
              NoSegmentation = True
        elif opt in ("--all-segmentation"):
              AllSegmentation = True        
        elif opt in ("--use_c3d"):
            use_c3d = True
    
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
    
    if verbose:
        msg = (
            f"Input path: {inpath}\n"
            f"Output path: {outpath}\n"
            f"n_jobs: {n_jobs}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"Suffix to use in the name of generated files: {suffix}\n"
            f"Interpolation method for the image: {interpolation}\n"
            f"Interpolation method for the mask: {mask_interpolation}\n"
            f"No segmentation: {NoSegmentation}\n"
            f"All data segmented: {AllSegmentation}\n"
            )
        
        if use_c3d:
            msg += f"Spatial Resampling with c3d program\n"
        else:
            msg +=f"Spatial Resampling with sitk library\n"
        
        msg += (
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose: {verbose}\n"
            )
        
        hprint_msg_box(msg=msg, indent=2, title=f"SPATIAL_RESAMPLING {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if inpath == '' or outpath == '':
        print("\033[31mERROR! Input and output folders need to be specified\033[0m", flush=True)
        sys.exit()
    elif inpath == outpath:
        print("\033[31mERROR! Input and output paths must be different\033[0m", flush=True)
        sys.exit()
    else:
        if n_jobs == 1:
           for patient in tqdm(glob.glob(inpath+"/*"),
                              ncols=100,
                              desc="NIFTI Spatial resampling",
                              bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                              colour="yellow"):
               process_patient(patient,outpath,size, interpolation, mask_interpolation, suffix, path_to_c3d, skip_files,include_files, verbose,log,NoSegmentation,AllSegmentation,use_c3d)
        else:
            with multiprocessing.Pool(n_jobs) as pool:
                tqdm(pool.starmap(process_patient,
                                  [(patient,outpath,size, interpolation, mask_interpolation, suffix, path_to_c3d, skip_files,include_files,verbose,log,NoSegmentation,AllSegmentation,use_c3d) for patient in glob.glob(inpath+"/*")]),
                            ncols=100,
                            desc="NIFTI Spatial resampling",
                            bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                            colour="yellow")
           
def process_patient(patient,outpath,size, interpolation, mask_interpolation, suffix, path_to_c3d,skip_files,include_files, verbose,log,NoSegmentation,AllSegmentation,use_c3d):           
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

    #make directory for patient in output folder
    if not os.path.exists(os.path.join(outpath,patientID)):
        os.makedirs(os.path.join(outpath,patientID))

    for patient_subdirectory in glob.glob(patient+"/*"):
        subdirectory=os.path.basename(patient_subdirectory)
        if verbose:
            print(patientID+": "+subdirectory,flush=True)
            
        #make directory for subfolder
        if not os.path.exists(os.path.join(outpath,patientID,subdirectory)):
            os.makedirs(os.path.join(outpath,patientID,subdirectory))
                
        nifti_files = glob.glob(patient_subdirectory + "/*nii.gz")
        if not nifti_files:
            print(f"\033[31mERROR! Empty directory for {patientID} {subdirectory}\033[0m ",flush=True)
        else:
            for nifti_file in glob.glob(patient_subdirectory+"/*nii.gz"):
                if not is_mask(nifti_file): # Skip if it's identified as a mask
                    if verbose:
                        hprint(f"Resampling Image {patientID} {subdirectory}", nifti_file)
                    input_img= os.path.join(patient_subdirectory,nifti_file)
                    output_img=os.path.join(outpath,patientID,subdirectory,os.path.splitext(os.path.splitext(os.path.basename(nifti_file))[0])[0]+"_"+suffix+".nii.gz")

                    if use_c3d:
                        arg_img="-interpolation "+interpolation+" -resample-mm "+str(float(size))+"x"+str(float(size))+"x"+str(float(size))+"mm"
                        arg_msk="-interpolation "+mask_interpolation+" -resample-mm "+str(float(size))+"x"+str(float(size))+"x"+str(float(size))+"mm"
                    
                        cmd = path_to_c3d+" "+input_img+ " " + arg_img + " -o " + output_img
                        try:
                            subprocess.run(shlex.split(cmd))
                        except Exception as e:
                            print("\033[31mERROR!\033[0m "+ cmd,flush=True)
                            print(e)
                    else:
                        try:
                            resample_image_sitk(input_img, output_img, size, interpolation,cast_type="float32")
                        except:
                            print("\033[31mERROR! Spatial resampling with sitk failed\033[0m", flush=True)
                            print(f"\033[31mSkipping image for {patientID}{subdirectory}\033[0m",flush=True)
           
            if verbose:
                print(patientID+": "+subdirectory+" masks",flush=True)
            if not NoSegmentation: #if there is mask to resample
                for nifti_file in glob.glob(patient_subdirectory+"/*nii.gz"):
                    if len(glob.glob(os.path.join(patient_subdirectory, "*nii.gz"))) > 1: #there is more than 1 nifti file
                        if is_mask(nifti_file): #Nifti identified as a mask
                            if verbose:
                                hprint(f"Resampling Mask {patientID} {subdirectory}", nifti_file)

                            input_msk= os.path.join(patient_subdirectory,nifti_file)
                            mask_name=os.path.splitext(os.path.splitext(os.path.basename(nifti_file))[0])[0]+"_"+suffix+".nii.gz"
                            output_msk=os.path.join(outpath,patientID,subdirectory,mask_name)
                            if use_c3d:
                                cmd = path_to_c3d+" "+ input_msk + " " + arg_msk + " -o " + output_msk
                                try:
                                    subprocess.run(shlex.split(cmd))
                                except Exception as e:
                                    print("\033[31mERROR!\033[0m "+cmd,flush=True)
                                    print(e)
                            else:
                                try:
                                    resample_image_sitk(input_msk, output_msk, size, mask_interpolation, cast_type="int8")
                                except:
                                    print("\033[31mERROR! Spatial resampling with sitk failed\033[0m", flush=True)
                                    print(f"\033[31mSkipping image for {patientID}{subdirectory}\033[0m",flush=True)
                    else:
                        if AllSegmentation: #all data need to be segemented
                            print("\033[31mERROR!: No segmentation found in the current subdirectory\033[0m",flush=True)
                            return
                        else:
                            print("\033[33mWARNING!: No segmentation found for data \033[0m"+patient_subdirectory,flush=True)
     

def is_mask(nifti_file, verbose=False):
    """
    Function to determine if a NIfTI file is a mask or an image based on the filename and the unique voxel intensities.
    The function first checks the filename for common keywords (e.g., 'img', 'msk').
    If verbose is True, it will print whether the file is identified as a mask or an image.
    """
    
    # Check the filename for common patterns
    filename = os.path.basename(nifti_file).lower()  # Convert to lowercase to avoid case sensitivity
    
    if 'img' in filename or 'image' in filename:
        if verbose:
            print(f"{nifti_file}: Identified as image based on filename.")
        return False  # Identified as an image
    
    if 'msk' in filename or 'mask' in filename:
        if verbose:
            print(f"{nifti_file}: Identified as mask based on filename.")
        return True  # Identified as a mask
    
    # If the filename doesn't give clear clues, check the voxel intensities
    img = nib.load(nifti_file)
    data = img.get_fdata()
    
    unique_values = np.unique(data)
    
    # Assume masks have few unique values, typically less than 10
    if len(unique_values) < 100:
        if verbose:
            print(f"{nifti_file}: Identified as mask based on unique values (fewer than 100 unique values).")
        return True  # Consider it a mask
    else:
        if verbose:
            print(f"{nifti_file}: Identified as image based on unique values (more than 100 unique values).")
        return False  # Consider it an image


def resample_image_sitk(input_path, output_path, size, interpolation_type, cast_type=None):
    # Load the image using SimpleITK
    image = sitk.ReadImage(input_path)

   # Optionally cast the image to the specified type
    if cast_type:
        if cast_type.lower() == "float32":
            image = sitk.Cast(image, sitk.sitkFloat32)
        elif cast_type.lower() == "int8":
            image = sitk.Cast(image, sitk.sitkInt8)
        elif cast_type.lower() == "int16":
            image = sitk.Cast(image, sitk.sitkInt16)
        elif cast_type.lower() == "uint8":
            image = sitk.Cast(image, sitk.sitkUInt8)
        elif cast_type.lower() == "uint16":
            image = sitk.Cast(image, sitk.sitkUInt16)
        else:
            raise ValueError(f"\033[31mERROR! Unsupported cast type: {cast_type}\033[0m")

    # Define the new spacing and calculate the new size
    original_size = image.GetSize()
    original_spacing = image.GetSpacing()
    new_spacing = [float(size)] * 3
    new_size = [
        int(round(original_size[0] * (original_spacing[0] / new_spacing[0]))),
        int(round(original_size[1] * (original_spacing[1] / new_spacing[1]))),
        int(round(original_size[2] * (original_spacing[2] / new_spacing[2])))
    ]

    # Set the resampler
    resampler = sitk.ResampleImageFilter()
    resampler.SetSize(new_size)
    resampler.SetOutputSpacing(new_spacing)
    resampler.SetOutputOrigin(image.GetOrigin())
    resampler.SetOutputDirection(image.GetDirection())

    # Choose interpolation type
    if interpolation_type.lower() == "nearestneighbor":
        resampler.SetInterpolator(sitk.sitkNearestNeighbor)
    elif interpolation_type.lower() == "linear":
        resampler.SetInterpolator(sitk.sitkLinear)
    elif interpolation_type.lower() == "cubic":
        resampler.SetInterpolator(sitk.sitkBSpline)
    elif interpolation_type.lower() == "sinc":
        resampler.SetInterpolator(sitk.sitkHammingWindowedSinc)
    elif interpolation_type.lower() == "gaussian":
        resampler.SetInterpolator(sitk.sitkGaussian)
    elif interpolation_type.lower() == "b-spline":
        resampler.SetInterpolator(sitk.sitkBSpline)
    else:
        raise ValueError(f"\033[31mERROR! Unsupported interpolation type: {interpolation_type}033[0m")

    # Execute the resampling
    resampled_image = resampler.Execute(image)

    # Save the resampled image
    sitk.WriteImage(resampled_image, output_path)

if __name__ == "__main__":
    main(sys.argv[1:])    
