#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
img2Radiomics follow the instructions in the config file to transform images and extract radiomics features 

Usage: img2radiomics.py -c <configFile>
Help: img2radiomics.py -h
"""

import os,sys, getopt
import pandas as pd
import subprocess
import time 
from datetime import datetime
from src.utils import eprint
from src.utils import print_msg_box
from src.utils import print_params 


def main(argv):
    configFile = ''
    configs=[] #list of configs for the radiomics feature extraction
    verbose = False
    log = ''
    inputPath = ''
    global_params = {}
    params = {}
    previous_outFolder = ''
    new_log = False
    
    try:
        opts, args = getopt.getopt(argv, "vhc:i:",["log=","new_log","verbose","help","config=","input="])
    except getopt.GetoptError:
        print('img2radiomics.py -c <configFile>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\timg2radiomics.py\n")
            print("SYNOPSIS")
            print("\tStructFolderCheck.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>]\n")
            print("DESRIPTION")
            print("\timg2Radiomics follow the instructions in the config file to transform images and extract radiomics features\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -c, --config: specify the path to the config file (see RADIOMICS_PIPELINE_EXAMPLE)")
            print("\t -i, --input: specify the path to an input folder; to use this option, the path for the input folder in the config file needs to be set to '.'")
            print("\t --log: stdout redirect to log file")
            print("\t --new_log: overwrite previous log file")


            sys.exit()
        elif opt in ("-c", "--config"):
            configFile = arg
        elif opt in ("-i", "--input"):
            inputPath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--log"):
            log= arg 
        elif opt in ("--new_log"):
            new_log= True     
            
    if not configFile:
        print("\033[31mError: Missing configuration file. Use -c or --config to specify the path to the config file.\033[0m",flush=True)
        sys.exit(2)
    
    if not os.path.isfile(configFile):
        print(f"\033[31mError: Configuration file '{configFile}' not found.\033[0m",flush=True)
        sys.exit(2)
    
    if log != '':
        if new_log:
            f = open(log,'w+')
        else:
            f = open(log,'a+')
        sys.stdout = f      
     
    if verbose:
        print("-" * 50,flush=True)
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),flush=True)
        print("Configuration file: "+configFile,flush=True)
        print("Verbose "+str(verbose),flush=True)
        print("log:",str(log),flush=True)   
        print("Overwrite previous log file: ",str(new_log),flush=True)
        print("\n",flush=True)

 
    read_config_file(configFile,configs,verbose)
    
    #Check for default parameters
    for cfg in configs:
        if cfg["function"]=='GLOBAL_PARAMETERS':
            for i in cfg.index:
                if i != 'function':
                    global_params[i]=parse(cfg[i])
            if verbose:
                print("\033[1m\nGLOBAL_PARAMETERS: \033[0m",flush=True)
                print_params(global_params)

    #run pipeline
    for cfg in configs:
        if cfg["function"]!='GLOBAL_PARAMETERS':
            params.clear()
            params = global_params.copy()
            for i in cfg.index:
                params[i]=parse(cfg[i])

            ################
            # CHECK FOLDER #
            ################
            if cfg["function"] == 'CHECK_FOLDER':
                #default values is missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'log' in params.keys():
                    params['log']=''           
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'with-segmentation' in params.keys():
                    params['with-segmentation']=True
                if not 'inputFolder' in params.keys():
                    print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                    sys.exit()                
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)

                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)

                prog=["python", "src/StructFolderCheck.py"]
                
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["--log",str(params['log'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log")     
                if not params['with-segmentation']:
                    flags.append("--no-segmentation")
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    result=subprocess.check_output(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                    if 'Folder is correctly structured for the image processing pipeline' in str(result):
                        global_params['Structure'] = "Ready"
                    elif 'Folder is correctly structured to be restructed with reorganize.py' in str(result):
                        global_params['Structure'] = "Ready_to_reorganize"
                    else:
                        global_params['Structure'] = "Invalid"
                        sys.exit()
                    if verbose:
                        print("\033[1mFOLDER STRUCTURE:\033[0m", global_params['Structure'],flush=True)
                except:
                    print("\033[31mERROR running the script StructFolderCheck.py\033[0m",flush=True)

            ##############
            # REORGANIZE #
            ##############
            elif cfg["function"] == 'REORGANIZE':
                #default values is missing parameters
                if not 'timer' in params.keys():
                    params['timer']=False
                if not 'with-segmentation' in params.keys():
                    params['with-segmentation']=True
                if not 'all-data-with-segmentation' in params.keys():
                    params['all-data-with-segmentation']=True
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']=''
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'inplace' in params.keys():
                    params['inplace']=False
                if not 'log' in params.keys():
                    params['log']=''             
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1       
                if not 'mv' in params.keys():   #TO CHECK if the can be removed: depreciated
                    params['mv']='False'
                
                
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                
                #print(global_params)
                if not 'Structure' in global_params.keys():
                    global_params['Structure'] = "Unknow"
                
                print("global_params['Structure']:: ",global_params['Structure'],flush=True)
                
                if global_params['Structure'] == "Invalid":
                    print("ERROR! Current folder cannot be reorganize",flush=True)
                    sys.exit()
                elif global_params['Structure'] == "Ready":
                    print("Current folder is already ready for processing",flush=True)
                    #No_reoganize.py: if reorganize is not needed this script update the name of input folder to match the output folder that whould have been created by reorganize.py
                    if params['inplace'] == False: #no need to rename if inplace == True
                        prog=["python", "src/no_reorganize.py"]
                    
                        #FLAGS
                        flags =["-i", str(params['inputFolder'])]
                        flags.extend(["-o",str(params['outputFolder'])])
                        flags.extend(["--log",str(params['log'])])
                        if params['mv']:
                           flags.append("--mv")
                        if params['verbose']:
                            flags.append("-v")
                        if params['new_log_file']:
                            flags.append("--new_log") 
                        prog.extend(flags)  
                        try:
                            if params['timer']:
                                tic = time.perf_counter()
                            subprocess.run(prog)
                            if params['timer']:
                                toc = time.perf_counter()
                                print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                        except:
                            print("\033[31mERROR running the script no_reorganize.py\033[0m",flush=True)   
                else:
                    prog=["python", "src/reorganize_multiprocessing.py"]
    
                    #FLAGS
                    flags =["-i", str(params['inputFolder'])]
                    flags.extend(["-o",str(params['outputFolder'])])
                    flags.extend(["--log",str(params['log'])])
                    if params['verbose']:
                        flags.append("-v")
                    if params['new_log_file']:
                        flags.append("--new_log") 
                    if not params['with-segmentation']:
                        flags.append("--no-segmentation")
                    if params['all-data-with-segmentation'] and params['with-segmentation']:
                            flags.append("--all-segmentation")
                    if params['inplace']:
                        flags.append("--inplace")   
                    if params['skip']!='':
                        flags.extend(["-S",str(params['skip'])])
                    if params['include']!='':
                        flags.extend(["--include",str(params['include'])])
                    flags.extend(["-j",str(params['multiprocessing'])])

                    prog.extend(flags)
                    try:
                        if params['timer']:
                            tic = time.perf_counter()
                        subprocess.run(prog)
                        if params['timer']:
                            toc = time.perf_counter()
                            print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                    except:
                        print("\033[31mERROR running the script reorganize.py\033[0m",flush=True)
            ###########
            # DCM2NII #
            ###########
            elif cfg["function"] == 'DCM2NII':
                #default values is missing parameters
                if not 'timer' in params.keys():
                    params['timer']=False
                if not 'with-segmentation' in params.keys():
                    params['with-segmentation']=True
                if not 'all-data-with-segmentation' in params.keys():
                    params['all-data-with-segmentation']=True
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        print('\033[31mERROR! No out folder specified\033[0m',flush=True)
                        sys.exit()               
                if not 'mask_regMatch' in params.keys():
                    params['mask_regMatch']=".*"
                if not 'log' in params.keys():
                    params['log']=''  
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
                
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)

                prog=["python", "src/dcm2nii_multiprocessing.py"]

                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["-m",str(params['mask_regMatch'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log") 
                if not params['with-segmentation']:
                    flags.append("--no-segmentation")
                if params['all-data-with-segmentation'] and params['with-segmentation']:
                    flags.append("--all-segmentation")
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script dcm2nii_multiprocessing.py\033[0m",flush=True)
           
            ######################
            # SPATIAL RESAMPLING #
            ######################
            elif cfg["function"] == 'SPATIAL_RESAMPLING':
                #default values if missing parameters
                if not 'timer' in params.keys():
                    params['timer']=False
                if not 'with-segmentation' in params.keys():
                    params['with-segmentation']=True
                if not 'all-data-with-segmentation' in params.keys():
                    params['all-data-with-segmentation']=True
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'use_c3d' in params.keys():
                    params['use_c3d']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        print('\033[31mERROR! No out folder specified\033[0m',flush=True)
                        sys.exit()   
                if not 'voxel_size' in params.keys():
                    params['voxel_size']=1  
                if not 'image_interpolation' in params.keys():
                    params['image_interpolation']='Linear'  
                if not 'mask_interpolation' in params.keys():
                    params['mask_interpolation']='NearestNeighbor'                                         
                if not 'suffix_name' in params.keys():
                    params['suffix_name']='111'  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  

                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)

                prog=["python", "src/NiftiSpatialResampling_multiprocessing.py"]

                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["-I",str(params['image_interpolation'])])
                flags.extend(["-M",str(params['mask_interpolation'])])
                flags.extend(["-M",str(params['mask_interpolation'])])
                flags.extend(["-s",str(params['voxel_size'])])
                flags.extend(["-e",str(params['suffix_name'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log")
                if params['use_c3d']:
                    flags.append("--use_c3d")
                if not params['with-segmentation']:
                    flags.append("--no-segmentation")
                if params['all-data-with-segmentation'] and params['with-segmentation']:
                    flags.append("--all-segmentation")    
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script NiftiSpatialResampling_multiprocessing.py\033[0m",flush=True)
                    
            ########################
            # INTENSITY RESAMPLING #
            ########################
            elif cfg["function"] == 'INTENSITY_RESAMPLING':
                #default values if missing parameters
                if not 'timer' in params.keys():
                    params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']=''
                if not 'image_filename' in params.keys():          
                    params['image_filename']='img.nii.gz'
                if not 'mask_filename' in params.keys():          
                    params['mask_filename']=''
                if not 'resampled_image_filename' in params.keys():
                    params['resampled_image_filename']='img_r.nii.gz'
                if not 'suffix_name' in params.keys():
                    params['suffix_name']=''  
                if not 'method' in params.keys():
                    params['method']='binning_number'
                if not 'n_bins' in params.keys():
                    params['n_bins']=256
                if not 'bin_width' in params.keys():
                    params['bin_width']=25
                if not 'min_scaling' in params.keys():
                    params['min_scaling']=0
                if not 'max_scaling' in params.keys():
                    params['max_scaling']=1
                if not 'lower_bound' in params.keys():
                    params['lower_bound']=2
                if not 'upper_bound' in params.keys():
                    params['upper_bound']=98                         
                if not 'suffix_name' in params.keys():
                    params['suffix_name']=''  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  

                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)

                prog=["python", "src/NiftiIntensityResampling_multiprocessing.py"]

                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["--img_name",str(params['image_filename'])])
                flags.extend(["--msk_name",str(params['mask_filename'])])
                flags.extend(["--resampled_img_name",str(params['resampled_image_filename'])])
                flags.extend(["-e",str(params['suffix_name'])])
                flags.extend(["--method",str(params['method'])])
                flags.extend(["--n_bins",str(params['n_bins'])])
                flags.extend(["--bin_width",str(params['bin_width'])])
                flags.extend(["--scale_min",str(params['min_scaling'])])
                flags.extend(["--scale_max",str(params['max_scaling'])])
                flags.extend(["--lower_bound",str(params['lower_bound'])])
                flags.extend(["--upper_bound",str(params['upper_bound'])])
                if params['verbose']:
                    flags.append("-v")  
                if params['new_log_file']:
                    flags.append("--new_log") 
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script NiftiSpatialResampling_multiprocessing.py\033[0m",flush=True)
                                                              
            ###############
            # MERGE MASKS #
            ###############   
            elif cfg["function"] == 'MERGE_MASKS':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']=''
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'image_filename' in params.keys():
                    params['image_filename']='img.nii.gz'
                if not 'resampled_image_filename' in params.keys():
                    params['resampled_image_filename']='r_img.nii.gz'
                if not 'mask_filename' in params.keys():
                    params['mask_filename']=''
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  
                if not('reg' in params.keys()) ^ ('add' in params.keys()):   
                    print('\033[31mERROR! To determine the masks to add and substract the options add and sub OR reg need to be used\033[0m',flush=True)
                    sys.exit()
                if 'add' in params.keys() and not 'sub' in params.keys():
                    params['sub']=''
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
                
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/NiftiMergeVolumes_multiprocessing.py"]

                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["-m",str(params['mask_name'])])
                if 'add' in params.keys():
                    flags.extend(["--add",str(params['add']),"--sub",str(params['sub'])])
                if 'reg' in params.keys():
                    flags.extend(["--reg",str(params['reg'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log") 
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script NiftiResampling_multiprocessing.py\033[0m",flush=True)  
 
                    
            #####################
            # MASK_THRESHOLDING #
            ##################### 
            elif cfg["function"] == 'MASK_THRESHOLDING':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('ERROR! No input folder specified',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']=''
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'image_filename' in params.keys():          
                    params['image_filename']='img.nii.gz'
                if not 'mask_filename' in params.keys():
                    params['mask_filename']='msk.nii.gz'
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''    
                if not 'suffix_name' in params.keys():
                    params['suffix_name']="mask_thresholding"  
                if not 'min_threshold' in params.keys():
                    params['min_threshold']=sys.float_info.min
                if not 'max_threshold' in params.keys():
                    params['max_threshold']=sys.float_info.max   
                
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/NiftiMaskThresholding_multiprocessing.py"]
           
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["-M",str(params['mask_filename'])])
                flags.extend(["-I",str(params['image_filename'])])
                flags.extend(["--min_thr",str(params['min_threshold'])])
                flags.extend(["--max_thr",str(params['max_threshold'])])
                flags.extend(["-e",str(params['suffix_name'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log") 
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])    
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script NiftiMaskThresholding_multiprocessing.py\033[0m",flush=True)   
            
            #####################
            # I-WINDOWING #
            ##################### 
            elif cfg["function"] == 'I-WINDOWING':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']=''
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'image_filename' in params.keys():          
                    params['image_filename']='img.nii.gz'
                if not 'windowed_image_filename' in params.keys():
                    params['windowed_image_filename']='img_w.nii.gz'
                if not 'window_name' in params.keys():
                    params['window_name']=''
                if not 'suffix_name' in params.keys():
                    params['suffix_name']=''  
                if not 'window_level' in params.keys():
                    params['window_level']=-5000   
                if not 'window_width' in params.keys():
                    params['window_width']=-5000 
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
 
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/NiftiWindowing_multiprocessing.py"]
           
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["--img_name",str(params['image_filename'])])
                flags.extend(["--windowed_img_name",str(params['windowed_image_filename'])])
                flags.extend(["--WL",str(params['window_level'])])
                flags.extend(["--WW",str(params['window_width'])])
                flags.extend(["--preset",str(params['window_name'])])
                flags.extend(["-e",str(params['suffix_name'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log")                
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])    
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script NiftiWindowing_multiprocessing.py\033[0m",flush=True)   
                    
            #####################
            # I-HARMONIZE #
            ##################### 
            elif cfg["function"] == 'I-HARMONIZE':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']=''
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'image_filename' in params.keys():          
                    params['image_filename']='img.nii.gz'
                if not 'mask_filename' in params.keys():          
                    params['mask_filename']=''
                if not 'reference_image' in params.keys():
                    print("\033[31mERROR! I-HARMONIZE requires a reference image to perform harmonization\033[0m",flush=True)
                    sys.exit(1)
                if not 'reference_mask' in params.keys():
                    params['reference_mask']=''
                if not 'harmonized_image_filename' in params.keys():
                    params['harmonized_image_filename']='h_img.nii.gz'
                if not 'method' in params.keys():
                    params['method']='histogram_matching'
                if not 'n_bins' in params.keys():
                    params['n_bins']=256
                if not 'n_matchPoints' in params.keys():
                    params['n_matchPoints']=10
                if not 'suffix_name' in params.keys():
                    params['suffix_name']=''
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
 
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/NiftiImageHarmonization_multiprocessing.py"]
           
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["--img_name",str(params['image_filename'])])
                flags.extend(["--msk_name",str(params['mask_filename'])])
                flags.extend(["--ref_img",str(params['reference_image'])])
                flags.extend(["--ref_msk",str(params['reference_mask'])])
                flags.extend(["--harmonized_img_name",str(params['harmonized_image_filename'])])
                flags.extend(["--method",str(params['method'])])
                flags.extend(["--n_bins",str(params['n_bins'])])
                flags.extend(["--n_matchPoints",str(params['n_matchPoints'])])
                flags.extend(["-e",str(params['suffix_name'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log")                
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])    
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script NiftiImageHarmonization_multiprocessing.py\033[0m",flush=True)  
                    
            ############################
            # N4-BIAS-FIELD-CORRECTION #
            ############################
            elif cfg["function"] == 'N4-BIAS-FIELD-CORRECTION':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']=''
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'image_filename' in params.keys():          
                    params['image_filename']='img.nii.gz'
                if not 'mask_filename' in params.keys():          
                    params['mask_filename']=''    
                if not 'corrected_image_filename' in params.keys():
                    params['corrected_image_filename']='img_n4biasCorr.nii.gz'
                if not 'bias_field_image_filename' in params.keys():
                    params['bias_field_image_filename']=''
                if not 'suffix_name' in params.keys():
                    params['suffix_name']=''
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
 
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/NiftiN4BiasFieldCorrection_multiprocessing.py"]
           
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["--img_name",str(params['image_filename'])])
                flags.extend(["--msk_name",str(params['mask_filename'])])
                flags.extend(["--corrected_img_name",str(params['corrected_image_filename'])])
                flags.extend(["--bias_field_name",str(params['bias_field_image_filename'])])
                flags.extend(["-e",str(params['suffix_name'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log")                
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])    
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script NiftiN4BiasFieldCorrection_multiprocessing.py\033[0m",flush=True)   
                    
                    
            ##############
            # RADIOMICS #
            ##############   
            elif cfg["function"] == 'RADIOMICS':
           
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'save_at_the_end' in params.keys():
                    params['save_at_the_end']=False
                if not 'stats_filename' in params.keys():
                     params['stats_filename']=''
                if not 'inputFolder' in params.keys():
                    print('ERROR! No input folder specified',flush=True)
                    sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder
                if not 'configs' in params.keys() and not 'pyradiomics_config' in params.keys():
                    print('\033[31mERROR! Neither "configs" nor "pyradiomics_config" is specified.\033[0m', flush=True)
                    sys.exit()
                else:
                    if not 'configs' in params.keys():
                        params['configs'] = ''
                    if not 'pyradiomics_config' in params.keys():
                        params['pyradiomics_config'] = ''
                if not 'outputFolder' in params.keys():
                    if 'outputFolderSuffix' in params.keys(): 
                        params['outputFolder']=params['inputFolder'].rstrip('/')+'_'+str(params['outputFolderSuffix'])
                    else:
                        params['outputFolder']='~/'
                if not 'image_filename' in params.keys():
                    params['image_filename']='img.nii.gz'
                if not 'mask_filename' in params.keys():
                    params['mask_filename']='msk.nii.gz'
                if not 'radiomics_filename' in params.keys():
                    params['radiomics_filename']='radiomics.xlsx'
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1
                if not 'log' in params.keys():
                    params['log']=''  
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''
                
                if params['save_at_the_end']==True and params['multiprocessing'] > 1:
                    params['save_at_the_end']=False
                    print("\033[33mWARNING: With multiprocessing option, radiomics results cannot be saved at the end. Save at the end was set to False\033[0m")
                
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/radiomics_multiprocessing.py"]
    
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                flags.extend(["-I",str(params['image_filename'])])
                flags.extend(["-M",str(params['mask_filename'])])
                flags.extend(["-R",str(params['radiomics_filename'])])
                flags.extend(["-c",str(params['configs'])])
                flags.extend(["-p",str(params['pyradiomics_config'])])
                flags.extend(["--stats_filename",str(params['stats_filename'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log") 
                if params['save_at_the_end']:
                    flags.append("-x")
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])        
                 
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script radiomics_multiprocessing.py\033[0m",flush=True)  
                  
                    
            ##########
            # DELETE #
            ##########   
            elif cfg["function"] == 'DELETE':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'log' in params.keys():
                    params['log']=''
                if not 'folder' in params.keys():
                    print('\033[31mERROR! No folder to delete\033[0m',flush=True)
                    sys.exit()                       
                if params['folder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['folder'] = previous_outFolder
                prog=["python", "src/delete_folder.py"]    
                
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                
                #FLAGS
                flags =["-f", str(params['folder'])]
                flags.extend(["--log",str(params['log'])])
                if params['verbose']:
                    flags.append("-v")
                
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script delete_folder.py\033[0m",flush=True)  
                        
                        
            ################
            # SEGMENTATION #
            ################          
            elif cfg["function"] == 'SEGMENTATION':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'skip-segmented-data' in params.keys():
                    params['skip-segmented-data']=False
                if not 'log' in params.keys():
                    params['log']=''
                if not 'inputFolder' in params.keys():
                    print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                    sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder   
                if not 'skip' in params.keys():
                    params['skip']=''
                if not 'include' in params.keys():
                    params['include']=''    
                if not 'multiprocessing' in params.keys():
                    params['multiprocessing']=1    
                if not 'method' in params.keys():
                    params['method']='TotalSegmentator'   
                if not 'segmentation-list' in params.keys():
                    params['segmentation-list']=''   
                if not 'image_type' in params.keys():
                    params['image_type']='nifti'   
                if not 'image_filename' in params.keys():
                    if params['image_type'] in('NIFTI','Nifti','nifti'):
                        params['image_filename']=''
                    else:
                        params['image_filename']='DCM'
                if not 'job_scheduler' in params.keys():
                    params['job_scheduler']='SGE'

                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/segmentation_multiprocessing.py"]
    
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-j",str(params['multiprocessing'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log") 
                if params['skip-segmented-data']:
                    flags.append("--skip-segmented-data")
                if params['skip']!='':
                    flags.extend(["-S",str(params['skip'])])
                if params['include']!='':
                    flags.extend(["--include",str(params['include'])])      
                flags.extend(["-m",str(params['method'])])
                flags.extend(["-f",str(params['segmentation-list'])])
                flags.extend(["-I",str(params['image_filename'])])
                flags.extend(["-t",str(params['image_type'])])
                flags.extend(["--job_scheduler",str(params['job_scheduler'])])

                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    global_params['with-segmentation']=True
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script radiomics_multiprocessing.py\033[0m",flush=True)  
            
            
            ##################
            #   F-NORMALIZE  #
            ##################          
            elif cfg["function"] == 'F-NORMALIZE':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'log' in params.keys():
                    params['log']=''
                if not 'inputFolder' in params.keys():
                    print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                    sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder   
                if not 'outputFolder' in params.keys():
                    params['outputFolder']=''
                if not 'modelFolder' in params.keys():
                    params['modelFolder']=''
                if not 'radiomics_filename' in params.keys():
                    params['radiomics_filename']='radiomics.xlsx'
                if not 'normalized_radiomics_filename' in params.keys():
                    params['normalized_radiomics_filename']='normalized_radiomics.xlsx'
                if not 'stats_filename' in params.keys():
                    params['stats_filename']=''                
                if not 'stratified' in params.keys():
                    params['stratified']='True'    
                if not 'method' in params.keys():
                    params['method']='MinMax'     
                if not 'mode' in params.keys():
                     params['mode']='Internal'     
                              
                
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/feature_normalization.py"]
    
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["-m",str(params['modelFolder'])])
                flags.extend(["-R",str(params['radiomics_filename'])])
                flags.extend(["-N",str(params['normalized_radiomics_filename'])])
                flags.extend(["-S",str(params['stats_filename'])])
                flags.extend(["-M",str(params['method'])])
                flags.extend(["--stratified",str(params['stratified'])])                
                flags.extend(["--norm_dataset",str(params['mode'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log") 
                    
                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script feature_normalization.py\033[0m",flush=True)      

            ##################
            #   F-HARMONIZE  #
            ##################          
            elif cfg["function"] == 'F-HARMONIZE':
                #default values if missing parameters
                if not 'timer' in params.keys():
                        params['timer']=False
                if not 'verbose' in params.keys():
                    params['verbose']=False
                if not 'new_log_file' in params.keys():
                    params['new_log_file']=False
                if not 'log' in params.keys():
                    params['log']=''
                if not 'inputFolder' in params.keys():
                    print('ERROR! No input folder specified',flush=True)
                    sys.exit()
                if params['inputFolder'] == '.':
                    if inputPath != '':
                        params['inputFolder']=inputPath
                    else:
                        print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
                if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                    params['inputFolder'] = previous_outFolder   
                if not 'outputFolder' in params.keys():
                    params['outputFolder']=''
                if not 'modelFolder' in params.keys():
                    params['modelFolder']=''
                if not 'radiomics_filename' in params.keys():
                    params['radiomics_filename']='radiomics.xlsx'
                if not 'batch_filename' in params.keys():
                        params['batch_filename']='radiomics.xlsx'
                if not 'harmonized_radiomics_filename' in params.keys():
                    params['harmonized_radiomics_filename']='harmonized_radiomics.xlsx' 
                if not 'radiomics_from_model_filename' in params.keys():
                    params['radiomics_from_model_filename']='' 
                if not 'batch_from_model_filename' in params.keys():
                    params['batch_from_model_filename']='' 
                if not 'estimates_filename' in params.keys():
                    params['estimates_filename']='' 
                if not 'ref_batch' in params.keys():
                    params['ref_batch']=None   
                if not 'mode' in params.keys():
                    params['mode']='internal'  
                if not 'covars' in params.keys():
                    params['covars']=''  
                    
                if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                    
                prog=["python", "src/feature_harmonization.py"]
    
                #FLAGS
                flags =["-i", str(params['inputFolder'])]
                flags.extend(["--log",str(params['log'])])
                flags.extend(["-o",str(params['outputFolder'])])
                flags.extend(["-m",str(params['modelFolder'])])
                flags.extend(["-r",str(params['radiomics_filename'])])
                flags.extend(["-b",str(params['batch_filename'])])
                flags.extend(["-R",str(params['harmonized_radiomics_filename'])])
                flags.extend(["-E",str(params['estimates_filename'])])
                flags.extend(["--radiomics_from_model",str(params['radiomics_from_model_filename'])])
                flags.extend(["--batch_from_model",str(params['batch_from_model_filename'])])
                flags.extend(["--ref_batch",str(params['ref_batch'])])
                flags.extend(["-M",str(params['mode'])])
                flags.extend(["--covars",str(params['covars'])])
                if params['verbose']:
                    flags.append("-v")
                if params['new_log_file']:
                    flags.append("--new_log") 

                prog.extend(flags)
                try:
                    if params['timer']:
                        tic = time.perf_counter()
                    subprocess.run(prog)
                    if params['timer']:
                        toc = time.perf_counter()
                        print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
                except:
                    print("\033[31mERROR running the script feature_harmonization.py\033[0m",flush=True)  
                    
               
            ##################
            #     PREDICT    #
            ##################          
            elif cfg["function"] == 'PREDICT':
               #default values if missing parameters
               if not 'timer' in params.keys():
                       params['timer']=False
               if not 'verbose' in params.keys():
                   params['verbose']=False
               if not 'new_log_file' in params.keys():
                   params['new_log_file']=False
               if not 'log' in params.keys():
                   params['log']=''
               if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
               if params['inputFolder'] == '.':
                   if inputPath != '':
                       params['inputFolder']=inputPath
                   else:
                       print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
               if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                   params['inputFolder'] = previous_outFolder   
               if not 'outputFolder' in params.keys():
                   params['outputFolder']=''
               if not 'modelFolder' in params.keys():
                   params['modelFolder']=''
               if not 'radiomics_filename' in params.keys():
                   params['radiomics_filename']='radiomics.xlsx'
               if not 'predict_filename' in params.keys():
                       params['predict_filename']='predict.xlsx'
               if not 'model_filename' in params.keys():
                   params['model_filename']='model.pkl'
                   
               if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                   
               prog=["python", "src/predict.py"]
   
               #FLAGS
               flags =["-i", str(params['inputFolder'])]
               flags.extend(["--log",str(params['log'])])
               flags.extend(["-o",str(params['outputFolder'])])
               flags.extend(["-m",str(params['modelFolder'])])
               flags.extend(["-r",str(params['radiomics_filename'])])
               flags.extend(["-p",str(params['predict_filename'])])
               flags.extend(["-M",str(params['model_filename'])])
               if params['verbose']:
                   flags.append("-v")
               if params['new_log_file']:
                   flags.append("--new_log") 
                   
               prog.extend(flags)
               try:
                   if params['timer']:
                       tic = time.perf_counter()
                   subprocess.run(prog)
                   if params['timer']:
                       toc = time.perf_counter()
                       print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
               except:
                   print("\033[31mERROR running the script predict.py\033[0m",flush=True)             
            
            ##################
            #     COPY       #
            ##################          
            elif cfg["function"] == 'COPY':
               #default values if missing parameters
               if not 'timer' in params.keys():
                       params['timer']=False
               if not 'verbose' in params.keys():
                   params['verbose']=False
               if not 'log' in params.keys():
                   params['log']=''
               if not 'inputFolder' in params.keys():
                   print('\033[31mERROR! No input folder specified\033[0m',flush=True)
                   sys.exit()
               if params['inputFolder'] == '.':
                   if inputPath != '':
                       params['inputFolder']=inputPath
                   else:
                       print("\033[31mERROR! If inputFolder is set to '.' img2radiomics needs to be use with -i option to select the input path\033[0m",flush=True)
               if params['inputFolder'] == 'PREVIOUS_BLOCK_OUTPUT_FOLDER':
                   params['inputFolder'] = previous_outFolder   
               if not 'targetFolder' in params.keys():
                   params['targetFolder']=''                   
               if verbose:
                    print(f"\033[1m\n{params['function']}\033[0m",flush=True)                    
                    print_params(params)
                   
               prog=["python", "src/copy_folder_contents.py"]
   
               #FLAGS
               flags =["-i", str(params['inputFolder'])]
               flags.extend(["--log",str(params['log'])])
               flags.extend(["-o",str(params['targetFolder'])])
               if params['verbose']:
                   flags.append("-v")

               prog.extend(flags)
               try:
                   if params['timer']:
                       tic = time.perf_counter()
                   subprocess.run(prog)
                   if params['timer']:
                       toc = time.perf_counter()
                       print(f"{params['function']} - Timer: {toc-tic:0.4f} seconds",flush=True)
               except:
                   print("\033[31mERROR running the script predict.py\033[0m",flush=True)  
                
        if 'outputFolder' in params.keys():
           if params['outputFolder'] != '':
               previous_outFolder=params['outputFolder']
            
                    
def read_config_file(config_File,configs,verbose):
    begin_param_list = False
    config=pd.Series(dtype=object)
    with open(config_File, 'r') as infile:
        for raw_line in infile:
            line=raw_line.strip()
            if not line: #skip empty line
                continue
            elif line[0] == '#':  #skip comment lines
                continue
            elif 'function' in config.index:
                if line[0]=='{':
                         begin_param_list = True
                elif begin_param_list == True:
                        if line[0]=='}':
                            configs.append(config)
                            if verbose:
                                print("\033[1mThe following instruction was found in",config_File,"\033[0m",flush=True)
                                print_params(config)
                            config=pd.Series(dtype=object)
                            begin_param_list = False
                        else:
                            line=line.replace(' ','')
                            line=line.replace('\t','')
                            try:
                                config=pd.concat([config,pd.Series(line.split('#')[0].split(':')[1], index=[line.split(':')[0]])])
                            except:
                                eprint("\033[31mERROR in the PIPELINE file ("+line+")\033[0m",flush=True)
                                print(f"\033[31mERROR in the PIPELINE file\033[0m (\033[36m{line}\033[0m)",flush=True)
                                sys.exit(1)
            elif 'GLOBAL_PARAMETERS' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('GLOBAL_PARAMETERS',index=["function"])])
            elif 'CHECK_FOLDER' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('CHECK_FOLDER',index=["function"])])
            elif 'REORGANIZE' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('REORGANIZE',index=["function"])])
            elif 'DCM2NII' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('DCM2NII',index=["function"])])
            elif 'SPATIAL_RESAMPLING' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('SPATIAL_RESAMPLING',index=["function"])])
            elif 'INTENSITY_RESAMPLING' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('INTENSITY_RESAMPLING',index=["function"])])    
            elif 'MERGE_MASKS' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('MERGE_MASKS',index=["function"])])
            elif 'MASK_THRESHOLDING' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('MASK_THRESHOLDING',index=["function"])])
            elif 'I-WINDOWING' in line.split('#')[0]:
                 config=pd.concat([config,pd.Series('I-WINDOWING',index=["function"])])
            elif 'I-HARMONIZE' in line.split('#')[0]:
                 config=pd.concat([config,pd.Series('I-HARMONIZE',index=["function"])])
            elif 'N4-BIAS-FIELD-CORRECTION' in line.split('#')[0]:
                 config=pd.concat([config,pd.Series('N4-BIAS-FIELD-CORRECTION',index=["function"])])
            elif 'RADIOMICS' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('RADIOMICS',index=["function"])])
            elif 'DELETE' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('DELETE',index=["function"])])
            elif 'SEGMENTATION' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('SEGMENTATION',index=["function"])])
            elif 'F-NORMALIZE' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('F-NORMALIZE',index=["function"])])
            elif 'F-HARMONIZE' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('F-HARMONIZE',index=["function"])])
            elif 'PREDICT' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('PREDICT',index=["function"])])      
            elif 'COPY' in line.split('#')[0]:
                config=pd.concat([config,pd.Series('COPY',index=["function"])])      
            else:
                print(f"\033[31mERROR!\033[0m The module \033[36m{line.split('#')[0]}\033[0m does not exist. Check the configuration file and documentation for more information on using PIPELINE files.",flush=True)
                sys.exit()
                
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
    
if __name__ == "__main__":
    main(sys.argv[1:])    
    
