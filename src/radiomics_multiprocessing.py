#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. _RADIOMICS:

The **RADIOMICS** module enables the extraction of radiomic features using the PyRadiomics library (https://pyradiomics.readthedocs.io/en/latest/).

Options
-------

The **RADIOMICS** module can be used with the following options:

- ``verbose``: Enable or disable verbose mode.
- ``timer``: Enable or disable the timer to record execution time.
- ``inputFolder``: Path to the input folder containing images.
- ``outputFolder``: Path to the output folder where radiomics results will be saved.
- ``outputFolderSuffix``: Adds a suffix to the input folder name to create an output folder.
- ``log``: Path to a file for saving logs.
- ``new_log_file``: Create a new log file; if a file with the same name already exists, it will be overwritten.
- ``skip``: Path to a file listing subfolders inside the input folder to exclude from processing.
- ``multiprocessing``: Specify the number of cores to use for parallel processing.
- ``configs``: Path to a radiomics configuration file, which can contain multiple configurations for PyRadiomics. See details in the next section :ref:`Radiomics_configuration_file`.
- ``pyradiomics_config``: Specify a PyRadiomics configuration file. Use this instead of ``configs`` if multiple configurations are unnecessary or if using PyRadiomics-specific preprocessing options.
- ``image_filename``: Name of the image file used for radiomic analysis.
- ``mask_filename``: Name of the mask (segmentation) file used for radiomic analysis.
- ``radiomics_filename``: Name of the Excel file that will store radiomics results.
- ``stats_filename``: Name of an optional Excel file to store statistics on radiomic features. If not specified, this file will not be created.
- ``save_at_the_end``: Specify whether the Excel file should be created only after processing all patients. Disabled by default, so new lines are added to the Excel file after processing each patient.

Example Usage
-------------

Below is an example of how to use the **RADIOMICS** module:

.. code-block:: bash

    RADIOMICS:
    {
        inputFolder: /path/to/NIFTI_folder
        outputFolder: /path/to/radiomics_results
        image_filename: img_111.nii.gz
        mask_filename: msk_111.nii.gz
        radiomics_filename: radiomics.xlsx
        save_at_the_end: false
        configs: /path/to/radiomics_config_file
        log: /path/to/logs/radiomics.log
    }

In this example:

- **inputFolder**: Specifies the folder containing the NIfTI images for radiomics analysis.
- **outputFolder**: Directory where radiomics results are stored.
- **image_filename**: Indicates the name of the image to be analyzed.
- **mask_filename**: Name of the mask file associated with the image.
- **radiomics_filename**: Designates the Excel file that will hold radiomics features extracted by PyRadiomics.
- **save_at_the_end**: If set to `false`, entries are written to the Excel file immediately after processing each patient.
- **configs**: Specifies the configuration file for PyRadiomics, allowing customization of feature extraction.
- **log**: Provides the path to the log file for recording the processing details.
"""

# Extract Radiomics features
#
# This script uses the PyRadiomics library to extract radiomics features using one or multiple configurations.
# The configurations are specified in a config file (see documentation for more details).
# Gabor decomposition is performed by this script and not by PyRadiomics.
# Usage:
#     radiomics_multiprocessing.py -i <inputfolder> -o <outputfolder> [options]
#
#__author__ Florent Tixier
#__email__ tixier@jhu.edu
#
# Options:
#   -h, --help                        Show this help message and exit
#   -v, --verbose                     Enable verbose output (default: False)
#   -i, --inputFolder <inputfolder>   Input folder with images to analyze
#   -o, --outputFolder <outputfolder> Output folder to save the results (default: ~/)
#   -c, --config <configfile>         File with a list of radiomics configurations for PyRadiomics (see CONFIGS_EXAMPLE)
#   -p, --pyradiomics_config <file>   A PyRadiomics configuration file (use instead of --config if only one configuration is needed)
#   -I, --img_filename <filename>     Name of images to analyze in the folder (default: img.nii.gz)
#   -M, --msk_filename <filename>     Name of masks to analyze in the folder (default: msk.nii.gz)
#   -R, --radiomics_filename <filename> Name of the Excel file to save radiomics features (default: radiomics.xlsx)
#       --stats_filename <filename>   Name of the Excel file to save radiomics statistics (optional)
#   -x                                Save Excel file with radiomics after processing all patients
#   -S, --skip <skip file path>       Path to file with filenames to skip
#       --include <include file path> Path to file with filenames to include (default: include all)
#       --log <log file path>         Redirect stdout to a log file
#       --new_log                     Overwrite previous log file
#   -j, --n_jobs <number of jobs>     Number of simultaneous jobs (default: 1)
#
# Help:
#     radiomics_multiprocessing.py -h

import sys, getopt, os
from tqdm import tqdm
import glob
import logging
import pandas as pd
import math
from math import pi
import SimpleITK as sitk
import multiprocessing
from radiomics import featureextractor
import re
from datetime import datetime
from utils import eprint
from utils import hprint_msg_box
from utils import hprint
from utils import format_list_multiline

def main(argv):
    inpath = ''
    outpath = '~/'
    configFile = ''
    configs=[] #list of configs for the radiomics feature extraction
    pyrconfigFile = ''
    img_filename= "img.nii.gz"
    msk_filename="msk.nii.gz"
    radiomics_filename = 'radiomics.xlsx'
    verbose = False
    n_jobs = 1
    skip_file_name=''
    skip_files=[]
    include_file_name=''
    include_files=[]
    save_xlsx_at_the_end= False
    features_df =pd.DataFrame() #dataframe for radiomics features
    log = ''
    new_log = False
    stats_filename= ''

    try:
        opts, args = getopt.getopt(argv, "vhi:o:c:p:j:I:M:R:S:x",["log=","new_log","verbose","skip=","include=","help","config=","pyradiomics_config=","inputFolder=","outFolder=","n_jobs=","img_filename=","msk_filename=","radiomics_filename=","stats_filename="])
    except getopt.GetoptError:
        print('Usage: radiomics_multiprocessing.py -i <inputfolder> -o <outputfolder> -c <configfile>')
        print('For help, use: radiomics_multiprocessing.py -h')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tradiomics_multiprocessing.py\n")
            print("SYNOPSIS")
            print("\tradiomics_multiprocessing.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>] [-I|--img_filename <img_filename>] [-M|--msk_filename <msk_filename>] [-R|--radiomics_filename <radiomics_filename>] [--stats_filename <stats_filename>] [-o|--outFolder <outFolder>] -c <configfile> [-x] [-S|--skip <skip>] [--include <include>] [--log <log>] [-j|--n_jobs <n_jobs>]")
            print("DESRIPTION")
            print("\tExtract Radiomics features for patients in the input folder with configurations in the config file\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with images to analyze")
            print("\t -I, --img_filename: name of images to analyze in the folder (default: img.nii.gz)")
            print("\t -M, --msk_filename: name of images to analyze in the folder (default: msk.nii.gz)")
            print("\t -R, --radiomics_filename: Name of the Excel file to save radiomics features (default: radiomics.xlsx)")
            print("\t --stats_filename: Name of the Excel file to save radiomics features")
            print("\t -o, --outFolder: Output folder to save the results (default: ~/)")
            print("\t -c, --config: File with a list of radiomics configurations for pyradiomics (see CONFIGS_EXAMPLE)")
            print("\t -p, --pyradiomics_config: A pyradiomics configuration file (to use instead of --config if there is no need of multiple configurations or to use preprocessing options of pyradiomics)")
            print("\t -x: Save Excel file with radiomics after processing all the patients")
            print("\t -S, --skip: Path to file with filenames to skip")
            print("\t --include: Path to file with filenames to include (all files included by default)",flush=True)
            print("\t --log: redirect stdout to a log file")
            print("\t --new_log: overwrite previous log file")
            print("\t -j, --n_jobs: Number of simultaneous jobs (default:1)")
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-I", "--img_filename"):
            img_filename = arg
        elif opt in ("-M", "--msk_filename"):
            msk_filename = arg
        elif opt in ("-R", "--radiomics_filename"):
            radiomics_filename = arg
        elif opt in ("--stats_filename"):
            stats_filename = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-x"):
            save_xlsx_at_the_end = True
        elif opt in ("-j", "--n_jobs"):
            n_jobs= int(arg)
        elif opt in ("-c","--config"):
            configFile = arg
        elif opt in ("-p","--pyradiomics_config"):
            pyrconfigFile = arg
        elif opt in ("-S","--skip"):
            skip_file_name= arg
        elif opt in ("--include"):
            include_file_name= arg
        elif opt in ("--log"):
            log= arg
        elif opt in ("--new_log"):
            new_log= True
    
    # set level for all classes
    logger = logging.getLogger("radiomics")
    logger.setLevel(logging.ERROR)
    
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
            print("ERROR! Unable to read the skip file")

    if include_file_name != '':
        try:
            file= open(include_file_name, 'r')
            include_files = file.read().splitlines() 
        except:
            print("ERROR! Unable to read the include file",flush=True) 
            
    if verbose:
        msg = (
            f"Input folder: {inpath}\n"
            f"Output folder: {outpath}\n"
            f"Images name: {img_filename}\n"
            f"Masks name: {msk_filename}\n"
            f"Configuration file: {configFile}\n"
            f"Pyradiomics Configuration file: {pyrconfigFile}\n"
            f"Radiomics Excel file name: {radiomics_filename}\n"
            f"Save Excel file at the end: {save_xlsx_at_the_end}\n"
            )
        
        if stats_filename != '':
            msg += f"Save an additional Excel file with radiomics statistics in: {stats_filename}\n"
        
        msg += (
            f"Skip file: {skip_file_name}\n"
            f"Files to skip: {format_list_multiline(skip_files,5)}\n"
            f"Include file: {include_file_name}\n"
            f"Files to include: {format_list_multiline(include_files,5)}\n"
            f"Verbose: {verbose}\n"
            f"n_jobs: {n_jobs}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            )
        hprint_msg_box(msg=msg, indent=2, title=f"RADIOMICS {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    #create outpath directory if needed
    if not os.path.exists(outpath):
        os.makedirs(outpath)      
    
    if configFile != '':
        try:
            read_config_file(configFile,configs,verbose)
            if verbose:
                print("Config file",configFile, " was read with success",flush=True)
        except:
            print("\033[31mERROR! Invalid config file\033[0m",flush=True)
            sys.exit()
    elif pyrconfigFile == '':
        print("A RADIOMICS_CONFIGS or a pyradiomics configuration file need to be specify",flush=True)
        sys.exit()

            
    if n_jobs == 1:
         for patient in tqdm(glob.glob(inpath+"/*"),
                         ncols=100,
                         desc="Extract Radiomics",
                         bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                         colour="yellow"):
             features_df=pd.concat([features_df,
                                    extract_radiomics(patient,inpath,outpath,img_filename,msk_filename,configs,pyrconfigFile,features_df,radiomics_filename,save_xlsx_at_the_end,n_jobs,skip_files,include_files,verbose,log)],
                                    axis=0)
             if save_xlsx_at_the_end==True:
                 features_df.to_excel(os.path.join(outpath,radiomics_filename),index=False)
    else:    
         with multiprocessing.Pool(n_jobs) as pool:
             tqdm(pool.starmap(extract_radiomics,
                               [(patient,inpath,outpath,img_filename,msk_filename,configs,pyrconfigFile,features_df,radiomics_filename,save_xlsx_at_the_end,n_jobs,skip_files,include_files,verbose,log) for patient in glob.glob(inpath+"/*")]),
                           ncols=100,
                           desc="Extract Radiomics",
                           bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                           colour="yellow")

         if merge_xlsx(outpath,radiomics_filename): #merge xslx file and delete temporary files (if success)
                 deleteTmp_xlsx(outpath)

    if stats_filename != '':
        radiomics_statistics(os.path.join(outpath,radiomics_filename), os.path.join(outpath,stats_filename), verbose, log)



def extract_radiomics(patient,inpath,outpath,img_filename,msk_filename,configs,pyrconfigFile,features_df,radiomics_filename,save_xlsx_at_the_end,n_jobs,skip_files,include_files,verbose,log):
    if log != '':
        f = open(log,'a+')
        sys.stdout = f
    
    patientID=os.path.basename(patient)
    patient_features_df =pd.DataFrame() #radiomics features for 1 patients

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
    
    for patient_subdirectory in glob.glob(patient+"/*"):
        first_cfg=True #to extract diagnosis info from the first radiomics config
        subdirectory=os.path.basename(patient_subdirectory)    
        features_subdir_df =pd.DataFrame() #radiomics features for 1 patients

        if verbose:
            print(patientID+": "+subdirectory,flush=True)
        
        try:
            img = sitk.ReadImage(os.path.join(patient_subdirectory,img_filename))
        except:
            print("\033[31mERROR! Image ",os.path.join(patient_subdirectory,img_filename), " was not read\033[0m",flush=True)
            print("\033[31mSkipping image"+patientID+" "+subdirectory+"\033[0m",flush=True)
            eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading image)")
            continue
        try:
            msk = sitk.ReadImage(os.path.join(patient_subdirectory,msk_filename))
            msk_array = sitk.GetArrayFromImage(msk)
            # Check if the mask is empty (all voxels are zero)
            if not msk_array.any():
                print(f"\033[31mERROR! Mask {os.path.join(patient_subdirectory, msk_filename)} is empty (all voxels = 0)\033[0m", flush=True)
                print(f"\033[31mSkipping image {patientID} {subdirectory}\033[0m", flush=True)
                eprint(f"Skipping {patientID} {subdirectory} (ERROR empty mask)")
                continue
        except:
            print("\033[31mERROR! Mask ",os.path.join(patient_subdirectory,msk_filename), " was not read\033[0m",flush=True)
            print("\033[31mSkipping image"+patientID+" "+subdirectory+"\033[0m",flush=True)
            eprint("Skipping "+patientID+" "+subdirectory+" (ERROR reading mask)")
            continue
        
        if pyrconfigFile != '': #use a pyradiomics config file
            if verbose:
                print(patientID+": "+subdirectory+" ("+pyrconfigFile+")",flush=True)        
            try:
                extractor= featureextractor.RadiomicsFeatureExtractor(pyrconfigFile)
                radiomics = extractor.execute(img, msk)
            except:
                print('\033[31mERROR radiomics feature extraction failed\033[0m',flush=True)
            try:
                features = {k: v for k, v in radiomics.items()}
                features_subdir_cfg_df = pd.DataFrame([features.values()], columns=features.keys())
                features_subdir_cfg_df.insert(loc=0, column='sub_Analysis', value=subdirectory)
                features_subdir_cfg_df.insert(loc=0, column='patientID', value=patientID)
                features_subdir_df = pd.concat([features_subdir_df, features_subdir_cfg_df], axis=1)
                
            except:
                print("\033[31mERROR reading radiomics items\033[0m",flush=True)
        else: #use RADIOMICS_CONFIGS file
            for cfg in configs:
                if verbose:
                    print(patientID+": "+subdirectory+" ("+cfg["configName"]+")",flush=True)
                
                params = {}
                for i in cfg.index:
                    params[i]=parse(cfg[i]) 
                
                if verbose:
                    print(params,flush=True)
                    
                if params['imageType'] == 'Original':
                    try:
                        extractor= featureextractor.RadiomicsFeatureExtractor(**params)
                        radiomics = extractor.execute(img, msk)
                    except:
                        print('\033[31mERROR radiomics feature extraction failed\033[0m',flush=True)
            
                elif params['imageType'] == 'Gabor':
                    try:
                        params['imageType']='Original' #For gabor the convolution is done outside pyradiomics 
                        extractor= featureextractor.RadiomicsFeatureExtractor(**params)
                        extractor.disableAllFeatures()
                        extractor.enableFeatureClassByName('firstorder')
                        extractor.enableFeatureClassByName('glcm')
                        extractor.enableFeatureClassByName('gldm')
                        extractor.enableFeatureClassByName('glrlm')
                        extractor.enableFeatureClassByName('glszm')
                        extractor.enableFeatureClassByName('ngtdm')
                        boundingBox=featureextractor.imageoperations.checkMask(sitk.Cast(img, sitk.sitkInt64),sitk.Cast(msk, sitk.sitkInt64))
                        if not 'padDistance' in params.keys():
                            params['padDistance']=10
                        cropImg, cropMsk = featureextractor.imageoperations.cropToTumorMask(img, msk, boundingBox[0], padDistance=params['padDistance'])
                        gabCropImg=gaborFilterImg(cropImg,params=params,ID=patientID+'_'+subdirectory,path=outpath)
                        radiomics = extractor.execute(gabCropImg, cropMsk)
    
                    except:
                        print('\033[31mERROR radiomics feature extraction failed\033[0m',flush=True)
                else:
                    try:
                        extractor = featureextractor.RadiomicsFeatureExtractor(**params)
                        extractor.disableAllImageTypes()
                        extractor.enableImageTypeByName(params['imageType'])
                        extractor.disableAllFeatures()
                        extractor.enableFeatureClassByName('firstorder')
                        extractor.enableFeatureClassByName('glcm')
                        extractor.enableFeatureClassByName('gldm')
                        extractor.enableFeatureClassByName('glrlm')
                        extractor.enableFeatureClassByName('glszm')
                        extractor.enableFeatureClassByName('ngtdm')
                        radiomics = extractor.execute(img, msk)
                    except:
                       print('\033[31mERROR radiomics feature extraction failed\033[0m',flush=True)
                if first_cfg:    #pull out diagnostic info from first configuration
                    first_cfg=False    
                    try:    
                        diagnostics = {k: v for k, v in radiomics.items() if (k.startswith('diagnostics'))}
                        diagnostics_df=pd.DataFrame([diagnostics.values()],columns=diagnostics.keys())
                        diagnostics_df.insert(loc=0,column='sub_Analysis',value=subdirectory)
                        diagnostics_df.insert(loc=0,column='patientID',value=patientID)
                        features_subdir_df= pd.concat([features_subdir_df,diagnostics_df], axis=1)
                    except:
                        print('\033[31mERROR reading diagnostic information\033[0m',flush=True)
            
                try:
                    features = {k: v for k, v in radiomics.items() if not(k.startswith('diagnostics'))}    
                    prefix=next(iter(features.keys())).split('_')[0].split('-')[0]
                    features = {k.removeprefix(prefix): v for k, v in features.items()}  #remove original from feature name
                    features ={f'{params["configName"]}{k}': v for k, v in features.items()} #add configName as a prefix to the features name
                    features_subdir_cfg_df=pd.DataFrame([features.values()],columns=features.keys())
                    features_subdir_df= pd.concat([features_subdir_df,features_subdir_cfg_df], axis=1)
                except:
                    print("\033[31mERROR reading radiomics items\033[0m",flush=True)
            
        if save_xlsx_at_the_end==False:
            if n_jobs == 1: #no multiprocessing
                try:
                    if not os.path.exists(os.path.join(outpath,radiomics_filename)):
                        features_subdir_df.to_excel(os.path.join(outpath,radiomics_filename),index=False)
                    else:
                        with pd.ExcelWriter(os.path.join(outpath,radiomics_filename), if_sheet_exists = 'overlay', mode='a') as writer:
                            features_subdir_df.to_excel(writer,startrow=writer.sheets['Sheet1'].max_row,index=False, header=False)
                except:
                    print("\033[31mERROR! patient "+patientID+" was not added in the excel file\033[0m",flush=True)
            else:
                try:
                        features_subdir_df.to_excel(os.path.join(outpath,".tmp___"+patientID+"___"+subdirectory+"___"+radiomics_filename),index=False)
                except:
                    print("\033[31mERROR! patient "+patientID+" was not added in the excel file ("+os.path.join(outpath,".tmp___"+patientID+"___"+subdirectory+"___"+radiomics_filename)+")\033[0m",flush=True)
        else:
            patient_features_df=pd.concat([patient_features_df, features_subdir_df], axis=0) #add subanalysis for the patient to feature_df
    hprint("Radiomics saved:", os.path.join(outpath,radiomics_filename))
    return patient_features_df
          

     

#Take a string and try to parse it to a list, a float, a int or a bool
def parse(i):
    if i in ['True','true']:        #Bool True
        return True
    elif i in ['False','false']:    #Bool False
        return False
    else:
        try:                        #int
            return int(i)           
        except:
            try:                    #float
                return float(i)
            except:
                if 'pi' in i:
                    try:
                        return eval(i)
                    except:
                        return i
                elif not i[0] == '[': #string
                    return i
                else:
                    try:                #list
                        split=i.split(',')
                        split[0]=split[0].strip("[")
                        split[len(split)-1]=split[len(split)-1].strip("]")
                        for j in range(len(split)):
                            split[j]=parse(split[j])
                        return split
                    except:              #string
                        return i           

def read_config_file(config_File,configs,verbose):
    config=pd.Series(dtype=object)
    with open(config_File, 'r') as infile:
        for raw_line in infile:
            line=raw_line.strip()
            if not line:
                if 'configName' and 'imageType' in config.index: #a config needs to contain at least a config name and an image type
                    configs.append(config)
                    if verbose:
                        print("\033[1mThe following configuration was found in",config_File,"\033[0m",flush=True)
                        print(config,flush=True)
                    config=pd.Series(dtype=object)
                continue
            elif line[0]=='#':
                continue
            elif 'configName' in line:
                line=line.strip('configName:')
                line=line.replace(' ','')
                line=line.replace('\t','')
                config=pd.concat([config,pd.Series(line, index=["configName"])])
            elif 'imageType' in line:
                line=line.strip('imageType:')
                line=line.replace(' ','')
                line=line.replace('\t','')
                config=pd.concat([config,pd.Series(line, index=["imageType"])])
            else:
                line=line.replace(' ','')
                line=line.replace('\t','')
                config=pd.concat([config,pd.Series(line.split(':')[1], index=[line.split(':')[0]])])
        if 'configName' and 'imageType' in config.index: #a config needs to contain at least a config name and an image type
            if verbose:
                print("\033[1mThe following configuration was found in",config_File,"\033[0m",flush=True)
                print(config,flush=True)    
            configs.append(config)



#function for gabor filtering
#This function should be used after cropping the image to reduce processing time
def gaborFilterImg(img,params,ID,path="~/"):
    #default values is missing parameters
    if not 'verbose' in params.keys():
        params['verbose']=False
    if not 'save' in params.keys():
            params['save']=False
    if not 'padDistance' in params.keys():
        params['padDistance']=10
    if not 'size' in params.keys():
        params['size']=8  
    if not 'freq' in params.keys():
        params['freq']=0.5
    if not 'angle' in params.keys():
        params['angle']=0      
    hsize=params['size']*0.5
    vecDirection= (math.cos(params['angle']), -math.sin(params['angle']), math.sin(params['angle']), math.cos(params['angle']))
    vecOrigin= (hsize-hsize*(math.cos(params['angle'])-math.sin(params['angle'])),hsize-hsize*(math.sin(params['angle'])+math.cos(params['angle'])))
    GaborKernel = sitk.GaborImageSource()
    GaborKernel.SetOutputPixelType(sitk.sitkFloat32)
    GaborKernel.SetDirection(vecDirection)
    GaborKernel.SetOrigin(vecOrigin)
    GaborKernel.SetSize([params['size']]*2)
    GaborKernel.SetSigma([params['size']*.2]*2)
    GaborKernel.SetMean([hsize]*2)
    GaborKernel.SetFrequency(params['freq'])
    KernelImg=GaborKernel.Execute()   
    if params['save']:
        if not os.path.exists(os.path.join(path,ID)):
            os.makedirs(os.path.join(path,ID))
        sitk.WriteImage(KernelImg, os.path.join(path,ID,"GaborKernel.nii.gz"))
    GaborFilter=sitk.ConvolutionImageFilter()
    img = sitk.Cast(img, sitk.sitkFloat32)
    GabImg = img
    if params['verbose']:
        for k in  tqdm(range(img.GetSize()[2]), ncols = 100, desc="Apply gabor filter", bar_format="{l_bar}{bar} [ time left: {remaining}, time spent: {elapsed}]"):
            try:
                GabImg[:,:,k]=GaborFilter.Execute(img[:,:,k], KernelImg)
            except Exception as e:
                print(e,flush=True)      
    else:
        for k in  range(img.GetSize()[2]):
            try:
                GabImg[:,:,k]=GaborFilter.Execute(img[:,:,k], KernelImg)
            except Exception as e:
                print(e,flush=True)          
    if params['save']:
        if not os.path.exists(os.path.join(path,ID)):
            os.makedirs(os.path.join(path,ID))
        sitk.WriteImage(GabImg, os.path.join(path,ID,"Gabor_img.nii.gz"))
    return GabImg

#merge temporary excel file in one file and delete temporary files    
def merge_xlsx(path,radiomics_filename):
   file_list = glob.glob(path+ "/.tmp___*.xlsx")
   try:
       excels=[pd.ExcelFile(name) for name in file_list]    
       frames = [x.parse(x.sheet_names[0],header=None,incex_col=None) for x in excels]
       #remove headers row except for the first xlsx
       frames[1:] = [df[1:] for df in frames[1:]]
       combined=pd.concat(frames)
   except:
       print("\033[31mERROR! Excel files were not read correctly\033[0m",flush=True)
   try:
       combined.to_excel(os.path.join(path,radiomics_filename), header=False, index=False)
       print("Excel files were merged with success",flush=True)
       return 1
   except:
       print("\033[31mERROR! Excel files were not merged\033[0m",flush=True)
       return -1


#Save radiomics statistics
def radiomics_statistics(xlsx_input_file, xlsx_output_file, verbose, log):
    if log != '':
        f = open(log, 'a+')
        sys.stdout = f
    
    try:    
        df = pd.read_excel(xlsx_input_file)
        
        # Define columns to exclude
        exclude_pattern = r'^(patientID|sub_Analysis)|diagnostics'
        radiomics_columns = [col for col in df.columns if not re.match(exclude_pattern, col)]
        
        # Calculate statistics for the entire dataset
        column_stats = df[radiomics_columns].describe()
        statistic_names = column_stats.index.tolist()
        statistic_df = pd.DataFrame(columns=df.columns)
        statistic_df = statistic_df.rename(columns={'patientID': 'statistics'})
        statistic_df['statistics'] = statistic_names
        statistic_df['sub_Analysis'] = 'all'  # Set 'all' for the overall statistics
        statistic_df.index = column_stats.index
        statistic_df[radiomics_columns] = column_stats
        
        # Handle sub_Analysis-specific statistics
        unique_values = df['sub_Analysis'].unique()
        for value in unique_values:
            if verbose:
                print(f"Calculating statistics for sub_Analysis = {value}", flush=True)
            
            # Filter the dataframe by the specific sub_Analysis value
            subset_df = df[df['sub_Analysis'] == value]
            subset_stats = subset_df[radiomics_columns].describe()
            
            # Prepare a new dataframe for this subset's statistics
            subset_stat_df = pd.DataFrame(columns=df.columns)
            subset_stat_df = subset_stat_df.rename(columns={'patientID': 'statistics'})
            subset_stat_df['statistics'] = statistic_names
            subset_stat_df['sub_Analysis'] = value  # Set the current sub_Analysis value
            subset_stat_df.index = subset_stats.index
            subset_stat_df[radiomics_columns] = subset_stats
            
            # Append the subset statistics to the main statistics dataframe
            statistic_df = pd.concat([statistic_df, subset_stat_df], ignore_index=True)
        
        # Check if output file exists, and create a timestamped version if it does
        if os.path.exists(xlsx_output_file):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            base_filename = os.path.basename(xlsx_output_file)
            filename, extension = os.path.splitext(base_filename)
            new_filename = f"{filename}_{timestamp}{extension}"
            if verbose:
                print("\033[33mWARNING!",xlsx_output_file, "already exists, results will be saved in", new_filename,"\033[0m", flush=True)
            xlsx_output_file = os.path.join(os.path.dirname(xlsx_output_file), new_filename)
            
        # Save the final statistics dataframe to Excel
        try:
            statistic_df.to_excel(xlsx_output_file, index=False)
            hprint("Radiomics statistics saved", xlsx_output_file)
        except:
            print("\033[31mERROR saving ", xlsx_output_file,"\033[0m", flush=True)
    
    except Exception as e:
        print("\033[31mERROR reading ", xlsx_input_file, ": ", str(e),"\033[0m", flush=True)


def deleteTmp_xlsx(path):
   file_list = glob.glob(path+ "/.tmp___*.xlsx")
   for name in file_list:
       os.remove(name)
       
if __name__ == "__main__":
    main(sys.argv[1:])   
