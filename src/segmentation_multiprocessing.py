#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `SEGMENTATION` module enables automatic segmentation of DICOM or NIfTI images. Currently, TotalSegmentator is the only supported method for segmentation. The module will submit a new job task for each patient using either **SGE** or **SLURM** job schedulers.

Options
-------

The `SEGMENTATION` module can be configured with the following options:

- **verbose**: Enable or disable verbose mode to display detailed process information.
- **timer**: Enable a timer to record the module's execution time.
- **inputFolder**: Path to the folder containing the input images.
- **log**: Path to save a log file with detailed information about the segmentation process.
- **new_log_file**: Create a new log file, overwriting any existing file with the same name.
- **skip**: Path to a file listing subfolders inside `inputFolder` to exclude from processing.
- **skip-segmented-data**: If set to True, the module will skip data that has already been segmented (default: False).
- **multiprocessing**: Specify the number of CPU cores to use for parallel processing.
- **method**: Specify the segmentation method (currently, only "TotalSegmentator" is supported).
- **segmentation-list**: Path to a file listing specific volumes to segment.
- **image_type**: Specify whether the input images are in "DICOM" or "NIFTI" format:
  - For **DICOM**, the module generates an RTSTRUCT file (`RTSTRUCT.dcm`) containing segmentations.
  - For **NIFTI**, the module creates separate segmentations for each structure listed in `segmentation-list`, named as `Mask_<structure_name>.nii.gz`.
- **image_filename**: Name of the image file to segment when working with NIfTI images. For DICOM images, the module looks for images in the "DCM" folder.
- **job_scheduler**: Select the job scheduler for batch processing ("SGE" or "SLURM").

Example Usage
-------------

The following example demonstrates how to use the `SEGMENTATION` module:

.. code-block:: bash

    SEGMENTATION:
    {
        inputFolder: /path/to/NIFTI_folder
        method: TotalSegmentator
        image_type: dicom
        segmentation-list: /path/to/img2radiomics/v0.8.4/list_totalSegmentator_full.txt
        log: /path/to/logs/segmentation.log
    }

In this example:

- **inputFolder**: Specifies the folder containing images to segment.
- **method**: Selects "TotalSegmentator" for autosegmentation.
- **image_type**: Specifies DICOM format, producing an RTSTRUCT file with segmentations.
- **segmentation-list**: Points to a list of structures for segmentation.
- **log**: Specifies a path for the log file.

"""

# Automatic segmentation of NIfTI or DICOM images.
#
# This module currently supports TotalSegmentator (use --method='TotalSegmentator').
# Future versions may support additional segmentation methods.
#
# Usage:
#     segmentation_multiprocessing.py -i <inputFolder> [-v] [-S <skipFile>] [--include <includeFile>] [-m <method>] 
#                                      [-f <segmentationFile>] [-I <imageName>] [-t <imageType>] [--log <logFile>] 
#                                      [--job_scheduler <scheduler>] [-j <numJobs>] [--skip-segmented-data]
#
# Options:
#     -h, --help                       Show this help message and exit
#     -v, --verbose                    Enable verbose output (default: False)
#     -i, --input <inputFolder>        Path to the folder containing images to segment
#     -S, --skip <skipFile>            Path to a file with filenames to skip during segmentation
#     --include <includeFile>          Path to a file with filenames to include (all files are included by default)
#     -m, --method <algorithm>         Segmentation algorithm to use (default: TotalSegmentator)
#     -f, --file_list_segmentations    File with the names of the segmentations to perform
#     -I, --img_name <imageName>       Name of the image to segment (default: img.nii.gz)
#     -t, --type <imageType>           Type of images to process (NIfTI or DICOM; default: NIfTI)
#     --skip-segmented-data            Skip segmentation of data that are already segmented (default: False)
#     --log <logFile>                  Redirect stdout to a log file
#     --new_log                        Overwrite previous log file if it exists
#     --job_scheduler <scheduler>      Job scheduler to use for segmentation tasks (SGE or SLURM; default: SGE)
#     -j, --n_jobs <numJobs>           Number of simultaneous jobs (default: 1). If a job scheduler is used, 
#                                      multiprocessing is not typically useful.
# Help:
#     segmentation_multiprocessing.py -h


import sys, getopt, os
from tqdm import tqdm
import glob
import multiprocessing
import subprocess
import time
from datetime import datetime
from utils import hprint_msg_box
from utils import hprint
from utils import eprint
from utils import format_list_multiline

def main(argv):
    inputFolder = ''
    verbose = False
    skip_file_name=''
    skip_files=[]
    include_file_name=''
    include_files=[]
    n_jobs=1
    log = ''
    method = 'TotalSegmentator'
    segmentation_file_name=''
    segmentation_list = []
    img_name = 'img.nii.gz'
    img_type= 'nifti'
    job_scheduler='SGE' 
    skipSegmented= False
    new_log = False

    try:
        opts, args = getopt.getopt(argv, "hvi:j:S:m:f:I:t:",["log=","new_log","verbose","help","input=","n_jobs=","skip=","include=","method=","file_list_segmentations=","img_name=","type=","job_scheduler=","skip-segmented-data"])
    except getopt.GetoptError:
        print('Usage: segmentation_multiprocessing.py -i <inputFolder> [-v] [-S <skipFile>] [--include <includeFile>] [-m <method>] [-f <segmentationFile>] [-I <imageName>] [-t <imageType>] [--log <logFile>] [--job_scheduler <scheduler>] [-j <numJobs>] [--skip-segmented-data]', flush=True)
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME",flush=True)
            print("\tsegmentation_mutiprocessing.py\n",flush=True)
            print("SYNOPSIS",flush=True)
            print("\tsegmentation_multiprocessing.py [-h|--help][-v|--verbose][-i|--input <inputfolder>][-m|--method <algorithm>][-j|--n_jobs <number of simultaneous jobs>]\n", flush=True)
            print("DESRIPTION",flush=True)
            print("\tAutomatic segmentation of NIfTI or DICOM images\n", flush=True)
            print("OPTIONS",flush=True)
            print("\t -h, --help: print this help page",flush=True)
            print("\t -v, --verbose: False by default",flush=True)
            print("\t -i, --input: input folder with images",flush=True)
            print("\t -S, --skip: path to file with filenames to skip",flush=True)
            print("\t --include: path to file with filenames to include (all files included by default)",flush=True)
            print("\t -m, --method: algorithm to use for segmentation (default: TotalSegmentator)", flush=True)
            print("\t -f, --file_list_segmentations: file with the name of the segmentations to perform",flush=True)
            print("\t -I, --img_name: name of the image to process (default: img.nii.gz)",flush=True)
            print("\t -t, --type: type of the images to process (NIfTI or DICOM, default: NIfTI)", flush=True)
            print("\t --skip-segmented-data: skip data that are already segmented", flush=True)
            print("\t --log: redirect stdout to a log file", flush=True)
            print("\t --new_log: overwrite previous log file", flush=True)
            print("\t --job_scheduler, use SGE or SLURM to schedule jobs (default SGE)",flush=True)
            print("\t -j, --n_jobs: number of simultaneous jobs (default: 1 - if a job_scheduler is used, multiprocessing is not useful)", flush=True)
            sys.exit()
        elif opt in ("-i", "--input"):
            inputFolder = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-j", "--n_jobs"):
            n_jobs= int(arg)
        elif opt in ("-S","--skip"):
            skip_file_name= arg
        elif opt in ("--include"):
            include_file_name= arg    
        elif opt in ("-f","--file_list_segmentations"):
            segmentation_file_name= arg
        elif opt in ("-I","--img_name"):
            img_name= arg
        elif opt in ("-m","--method"):
            method= arg
        elif opt in ("-t","--type"):
            img_type= arg
        elif opt in ("--log"):
            log= arg
        elif opt in ("--new_log"):
            new_log= True
        elif opt in ("--job_scheduler"):
            job_scheduler = arg
        elif opt in ("--skip-segmented-data"):
            skipSegmented = True  
                
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
    
    if segmentation_file_name != '':
        try:
            file= open(segmentation_file_name, 'r')
            segmentation_list = file.read().splitlines() 
        except:
            print("\033[31mERROR! Unable to read the segmentation list file\033[0m",flush=True)
    else:
        print("Please use -f or --file_list_segmentations to provide a file containing the name of the segmentations to perform",flush=True)

    if verbose:
        msg = (
            f"Input folder: {inputFolder}\n"
            f"n_jobs: {n_jobs}\n"
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"Method: {method}\n"
            f"File with list of segmentation: {segmentation_file_name}\n"
            f"Structures to segment: {format_list_multiline(segmentation_list,5)}\n"
            f"Image type: {img_type}\n"
            f"Skip segmented data: {skipSegmented}\n"
            f"Job scheduler: {job_scheduler}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Verbose:  {verbose}\n"
            )
        
        hprint_msg_box(msg=msg, indent=2, title=f"SEGMENTATION {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if n_jobs == 1:
        for patient in tqdm(glob.glob(inputFolder+"/*"),
                            ncols=100,
                            desc="Perform image segmentation",
                            bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                            colour="yellow"):
            image_segmentation(inputFolder,patient,img_name,img_type,method,segmentation_list,skip_files,include_files,skipSegmented, verbose,log,job_scheduler)
    else:    
        with multiprocessing.Pool(n_jobs) as pool:
            tqdm(pool.starmap(image_segmentation,
                              [(inputFolder,patient,img_name,img_type,method,segmentation_list,skip_files,include_files,skipSegmented, verbose,log,job_scheduler) for patient in glob.glob(inputFolder+"/*")]),
                          ncols=100,
                          desc="Perform image segmentation",
                          bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                          colour="yellow")
    while True: #Wait jobs for segmentation are completed before exiting
        if os.path.exists(os.path.join(inputFolder,'job_ids.txt')):
            try:
                with open(os.path.join(inputFolder,'job_ids.txt'), 'r') as file:
                    if not file.read():
                        if verbose:
                            print("Segmentations completed", flush=True)
                        break #exit loop when all job_id are completed and removed from job-ids.txt
                    else:
                        if verbose:
                            print("Segmentation jobs are currently pending/running",flush=True)
            except:
                print("\033[33mWARNING! Unable to open the file 'job_ids.txt'. Please check your data to verify if segmentation was performed correctly.\033[0m", flush=True)
        else:
            print("\033[33mWARNING! The file 'job_ids.txt' was not found. Data were probably not segmented correctly.\033[0m", flush=True)
            break
        remove_finished_jobs(inputFolder,job_scheduler)
        time.sleep(60)
     
    #Remove job_ids.txt after completed the segmentations
    try:
        os.remove(os.path.join(inputFolder,'job_ids.txt'))
    except:
        print("\033[33mWARNING! The file 'job_ids.txt' was not removed\033[0m", flush=True)
    
    #add prefix Mask_ at the begining of the name of all segmentation
    print("Add prefix to segmentation names",flush=True)
    for patient in tqdm(glob.glob(inputFolder+"/*"),
                        ncols=100,
                        desc="Rename segmentations",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
        add_prefix(patient,segmentation_list,img_type)
    


def image_segmentation(path,patient,img_name, img_type, method,segmentation_list,skip_files,include_files,skipSegmented, verbose,log,job_scheduler):
    if log != '':
        f = open(log,'a+')
        sys.stdout = f
        
    ListSegmentationsString = " ".join(str(item) for item in segmentation_list)
    patientID=os.path.basename(patient)

    if len(include_files) > 0: #if file to include are specify
        if patientID not in include_files: #if patient is to be excluded
            if verbose:
                print("\n" + patientID + " (" + patient + ") is not in the list of patients to include", flush=True)
            return 
    
    if len(skip_files) > 0: #if there are files to skip
        if patientID in skip_files:
            if verbose:
                print("\nskip "+patientID+" ("+patient+")",flush=True)
            return
    if verbose:
        hprint(f"Processing {patientID}", patient)
        
    for patient_subdirectory in glob.glob(patient+"/*"):
        subdirectory=os.path.basename(patient_subdirectory)
        if verbose:
                print(patientID+": "+subdirectory,flush=True)
        
        if not skipSegmented or (img_type.lower()=='dicom' and not os.path.exists(os.path.join(patient_subdirectory, "RTSTRUCT.dcm"))) or (len(glob.glob(os.path.join(patient_subdirectory, "*nii.gz"))) < 2) : #run the segmentation if there is no rules to skip segmented data or data or check if data are not already segmented (RTSTRUCT file or more than one nifti file)
            if method == 'TotalSegmentator':
                if job_scheduler in ('SGE','Sge','sge'):
                    try: 
                        cmd = "qsub -terse SGE/qsub_TotalSegmentator_GPU.sh " + img_type +" "+os.path.join(patient_subdirectory,img_name) +" " + patient_subdirectory + " " + '"' + ListSegmentationsString + '"'
                        job_id=subprocess.check_output(cmd,shell=True)
                        print("JOB_ID=",str(job_id.decode().strip()),flush=True)
                        with open(os.path.join(path,"job_ids.txt"),'a+') as f:
                            f.write(str(job_id.decode().strip())+'\n')
                    except:
                        print("\033[31mERROR! Total Segmentator did not run properly\033[0m",flush=True)
                        print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                        eprint("Skipping "+patientID+" "+subdirectory+" (ERROR TotalSegmentator)")
                        continue
                elif job_scheduler in ('SLURM','Slurm','slurm'):
                    try:
                        cmd = "sbatch SLURM/sbatch_TotalSegmentator_GPU.sh " + img_type +" "+os.path.join(patient_subdirectory,img_name) +" " + patient_subdirectory + " " + '"' + ListSegmentationsString + '"'
                        job_id=subprocess.check_output(cmd,shell=True)
                        print('JOB_ID=',str(job_id.decode().strip().split()[-1]),flush=True)
                        with open(os.path.join(path,"job_ids.txt"),'a+') as f:
                            f.write(str(job_id.decode().strip().split()[-1])+'\n')
                    except:
                        print("No GPU available, trying with CPU.")
                        try:
                            cmd = "sbatch SLURM/sbatch_TotalSegmentator_CPU.sh " + img_type +" "+os.path.join(patient_subdirectory,img_name) +" " + patient_subdirectory + " " + '"' + ListSegmentationsString + '"'
                            job_id=subprocess.check_output(cmd,shell=True)
                            with open(os.path.join(path,"job_ids.txt"),'a+') as f:
                                f.write(str(job_id.decode().strip().split()[-1])+'\n')
                                f.close()
                        except:
                            print("\033[31mERROR! Total Segmentator did not run properly\033[0m", flush=True)
                            print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                            eprint("Skipping "+patientID+" "+subdirectory+" (ERROR TotalSegmentator)")
                            continue
                elif job_scheduler in ('NONE','None','none'):
                    try:
                        cmd = "NoJobScheduler/TotalSegmentator_GPU.sh " + img_type +" "+os.path.join(patient_subdirectory,img_name) +" " + patient_subdirectory + " " + '"' + ListSegmentationsString + '"'
                        job_id=subprocess.Popen(cmd, shell=True)
                        print('JOB_ID=',str(job_id.pid),flush=True)
                        with open(os.path.join(path,"job_ids.txt"),'a+') as f:
                            f.write(str(job_id.pid)+'\n')
                            f.close()
                    except:
                        print("No GPU available, trying with CPU.")
                        try:
                            cmd = "NoJobScheduler/TotalSegmentator_CPU.sh " + img_type +" "+os.path.join(patient_subdirectory,img_name) +" " + patient_subdirectory + " " + '"' + ListSegmentationsString + '"'
                            job_id=subprocess.Popen(cmd, shell=True)
                            with open(os.path.join(path,"job_ids.txt"),'a+') as f:
                                f.write(str(job_id.pid)+'\n')
                                f.close()
                        except:
                            print("\033[31mERROR! Total Segmentator did not run properly\033[0m", flush=True)
                            print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m",flush=True)
                            eprint("Skipping "+patientID+" "+subdirectory+" (ERROR TotalSegmentator)")
                            continue
                else:
                    print("\033[31mERROR! The job scheduler", job_scheduler, "is not available\033[0m", flush=True)                        
            else:
                print("\033[31mERROR! Segmentation algorithm", method, "is not available\033[0m", flush=True)
        else:
            print("\033[33mWARNING!: Skip segmentation for "+patient_subdirectory,"\033[0m",flush=True)
 
                        
def add_prefix(patient,segmentation_list,img_type):
    #add prefix Mask_ at the begining of the name of all segmentation
    segmentation_list_lower = [name.lower() for name in segmentation_list]
    for patient_subdirectory in glob.glob(patient+"/*"):
        if img_type == 'dicom':
                    os.rename(os.path.join(patient_subdirectory,'segmentations.dcm'),os.path.join(patient_subdirectory,'RTSTRUCT.dcm'))  
        else: #nifti
            for filename in os.listdir(patient_subdirectory):
                filename_without_extension_lower= filename.split('.')[0].lower()
                if filename_without_extension_lower in segmentation_list_lower:
                    new_filename = f'Mask_{filename}'
                    os.rename(os.path.join(patient_subdirectory,filename),os.path.join(patient_subdirectory,new_filename))  
               
   
def remove_finished_jobs(path,job_scheduler):
    if job_scheduler in ('SGE','Sge','sge'):
        current_job_ids=subprocess.check_output("qstat | awk '{print $1}'",shell=True)
    elif job_scheduler in ('SLURM','Slurm','slurm'):
        current_job_ids=subprocess.check_output("squeue -u $(whoami) | awk '{print $1}'",shell=True)
    elif job_scheduler in ('NONE','None','none'):
        current_job_ids=subprocess.check_output("pgrep -u $(whoami)", shell=True)
    else:
        print("\033[31mERROR! The job scheduler ",job_scheduler," is not available\033[0m",flush=True)
        current_job_ids=''
    list_current_job_ids=current_job_ids.decode().split('\n') #add [2:] at the end to remove to header lines
    try:
        with open(os.path.join(path,'job_ids.txt'),'r') as file, open(os.path.join(path,'.tmp_job_ids.txt'),'w') as tmp:
            for line in file:
                try:
                    id_value = str(line.rstrip())
                    if not id_value in list_current_job_ids:
                        continue #not copy this line in tmp file
                    tmp.write(line)
                except:
                    print("\033[31mERROR! Check the job_ids.txt file\033[0m", flush=True)
        os.rename(os.path.join(path,'.tmp_job_ids.txt'),os.path.join(path,'job_ids.txt'))
    except:
        sys.exit()
                

if __name__ == "__main__":
    main(sys.argv[1:])   
