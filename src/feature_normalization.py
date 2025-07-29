#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The `F-NORMALIZE` module allows for feature normalization. Normalization can be performed either internally, using statistics from the input Excel file, or externally, using statistics from another set of radiomics data. This module supports various normalization types, including Min-Max normalization, Z-Score normalization, and robust normalization (which removes the median and scales the data based on the quantile range).

The `F-NORMALIZE` module utilizes data from an input folder (`inputFolder`) and saves results in an output folder (`outputFolder`). If the output folder is not specified, results are saved in the input folder. When using the module in external mode, an additional folder (`modelFolder`) must be specified, containing files with the necessary statistics for normalization. Refer to the figure below for more details.

.. image:: img/f-normalize_folders.jpg
    :width: 400
    :alt: f-normalize_folders.jpg

Options
-------

The `F-NORMALIZE` module can be used with the following options:

- **verbose**: Enable or disable verbose mode.
- **timer**: Enable or disable the timer to record execution time.
- **log**: Specify the path to a file for saving logs.
- **new_log_file**: Create a new log file; if a log file with the same name already exists, it will be overwritten.
- **inputFolder**: Path to the input folder.
- **outputFolder**: Path to the output folder.
- **modelFolder**: Path containing data from a previously built model (optional, used with `mode: External`).
- **radiomics_filename**: Name of the Excel file with radiomics results.
- **stats_filename**: Name of an Excel file with statistics to use for normalization (optional, used with `mode: External`).
- **normalized_radiomics_filename**: Name of the Excel file created to store normalized radiomics results (default: `normalized_radiomics.xlsx`).
- **stratified**: Perform normalization using the statistics of each `sub_Analysis` separately (default: True).
- **method**: Method for feature normalization. Options are `MinMax` for Min-Max normalization, `Z-Score` for Z-Score normalization, and `RobustScaling` for robust normalization. Default: `MinMax`.
- **mode**: Perform normalization using the radiomics file (`Internal`, the default) or statistics computed on another radiomics file (`External`).

Example Usage
-------------

The following example demonstrates how to use the `F-NORMALIZE` module to perform a Z-Score normalization using statistics from an external training dataset:

.. code-block:: bash

    F-NORMALIZE
    {
        inputFolder: /path/to/radiomics_results
        # no output folder specified: saves output in the input folder
        modelFolder: /path/to/radiomics_model
        radiomics_filename: radiomics.xlsx
        normalized_radiomics_filename: normalized_radiomics.xlsx
        stats_filename: radiomics_stats_training.xlsx
        stratified: True
        method: Z-Score
        mode: external
        log: /path/to/logs/F-normalize.log
    }

"""
# Normalize radiomics features using various methods including Min-Max, Z-Score, and Robust Scaling.
# The script can use either internal statistics from the radiomics file itself or external statistics from a separate file.
#
# Usage:
#     feature_normalization.py -i <inputfolder> --radiomics_filename <radiomics excel file>
#
# Options:
#   -h, --help                         Show this help message and exit
#   -v, --verbose                      Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder>    Path to the input folder
#   -o, --outputFolder <outputFolder>  Path to the output folder
#   -m, --modelFolder <modelFolder>    Folder with model data for external normalization (when norm_dataset = 'external')
#   -R, --radiomics_filename           Name of the radiomics Excel file
#   -N, --normalized_radiomics_filename  Name for the output Excel file with normalized features
#   -S, --stats_filename               Name of the Excel file with statistics for external normalization (if norm_dataset = 'external')
#   -M, --method                       Normalization method: 'MinMax', 'Z-Score', or 'RobustScaling' (default: MinMax)
#       --norm_dataset                 Specify normalization mode: 'internal' (default) or 'external' for external statistics
#       --stratified                   Use stratified normalization based on each sub-analysis (default: True)
#       --log <logfile>                Redirect stdout to a log file
#       --new_log                      Overwrite the existing log file if it exists
#
# Help:
#     feature_normalization.py -h

import os,sys, getopt
import re
import pandas as pd
from datetime import datetime
from utils import hprint
from utils import hprint_msg_box

def main(argv):
    verbose = False
    log = ''
    inputPath = ''
    outputPath =''
    modelpath = ''
    radiomics_filename = 'radiomics.xlsx'
    normalized_radiomics_filename = 'normalized_radiomics.xlsx'
    stats_filename = ''
    method='MinMax'
    norm_dataset='internal'
    stratified = True
    new_log = False
    
    try:
        opts, args = getopt.getopt(argv, "vhR:i:o:S:N:M:m:",["log=","new_log","verbose","help","radiomics_filename=","normalized_radiomics_filename=","stats_filename=","inputFolder","outputFolder","stratified=","method=","norm_dataset=","modelFolder="])
    except getopt.GetoptError:
        print('feature_normalization.py -i <inputfolder> --radiomics_filename <radiomics excel file>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tnormalize.py\n")
            print("SYNOPSIS")
            print("\feature_normalization.py [-h|--help][-v|--verbose][-i|--inputFolder <inputfolder>]\n")
            print("DESRIPTION")
            print("\tNormalize radiomics features in an Excel file and save a new Excel file with normalized features\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -c, --config: <configFile> (see RADIOMICS_PIPELINE_EXAMPLE)")
            print("\t -i, --inputFolder: path the input folder")
            print("\t -o, --outputFolder: path the output folder")
            print("\t -m, --modelFolder: Folder with model results (to be used with 'norm_dataset' = external)")
            print("\t -R, --radiomics_filename: Filename of the radiomics file")
            print("\t -N, --normalized_radiomics_filename: Filename of the Excel file to save the normalized radiomics features")
            print("\t -S, --stats_filename: Filename with statistics to use for the normalization")
            print("\t -M, --method: Normalization method {MinMax, Z-Score, RobustScaling}, default: MinMax")
            print("\t --norm_dataset: Normalization using statistics from radiomics_filename (internal) or from statistics on radiomics previously computed (external), default value: internal")
            print("\t --log: redirect stdout to a log file")
            print("\t --new_log: overwrite previous log file", flush=True)
            sys.exit()
        
        elif opt in ("-i", "--inputFolder"):
            inputPath = arg
        elif opt in ("-o", "--outputFolder"):
            outputPath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--log"):
            log= arg 
        elif opt in ("--new_log"):
            new_log= True   
        elif opt in ("-R", "--radiomics_filename"):
            radiomics_filename=arg
        elif opt in ("-N", "--normalized_radiomics_filename"):
            normalized_radiomics_filename=arg
        elif opt in ("-S", "--stats_filename"):
            stats_filename=arg        
        elif opt in ("-M", "--method"):
            method=arg   
        elif opt in ("--norm_dataset"):
            norm_dataset=arg
        elif opt in ("--stratified"):
            if arg in ('false','False', 'FALSE', 'no', '0'):
                stratified = False
            else:
                stratified = True
            stratified=arg    
        elif opt in ("-m", "--modelFolder"):
            modelpath = arg
            
    if log != '':
        if new_log:
            f = open(log,'w+')
        else:
            f = open(log,'a+')
        sys.stdout = f      
    
    if inputPath == '':
        print("\033[31mERROR! Input path needs to be specified\033[0m",flush=True)
        sys.exit()

    if outputPath == '':
        if verbose:
            print(f"\033[33mWARNING! No output path specified, results will be save in the input path: {inputPath}\033[0m",flush=True)
        outputPath = inputPath
    
    if norm_dataset not in ('Internal','internal', 'INTERNAL') and stats_filename == '':
        print("\033[31mERROR: Normalization using data from an external dataset requires an Excel file with statistics. Please use the option '--stats_filename' or set 'norm_dataset' to 'Internal'\033[0m",flush=True)
        sys.exit()
    
    if verbose:
        msg = (
            f"Verbose: {verbose}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Input folder: {inputPath}\n"
            f"Output folder: {outputPath}\n"
            f"Model folder: {modelpath}\n"
            f"Radiomics file: {radiomics_filename}\n"
            )
        if stats_filename != '':
            msg += f"Statistics file: {stats_filename}\n"
        msg += (
            f"Normalization method: {method}\n"
            f"Stratified normalization: {stratified}\n"
            f"Normalization dataset: {norm_dataset}\n"
            f"Save normalized radiomics features in {normalized_radiomics_filename}\n"
            )
        
        hprint_msg_box(msg=msg, indent=2, title=f"F-NORMALIZE {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    perform_normalization(inputPath, radiomics_filename, modelpath, stats_filename, outputPath, normalized_radiomics_filename, norm_dataset, method, verbose, stratified)
   

def perform_normalization(inputPath, radiomics_filename, modelpath, stats_filename, outputPath, normalized_radiomics_filename, norm_dataset, method, verbose, stratified):
    radiomics = pd.read_excel(os.path.join(inputPath, radiomics_filename))
    exclude_pattern = r'^(patientID|sub_Analysis)|diagnostics'
    radiomics_columns = [col for col in radiomics.columns if not re.match(exclude_pattern, col)]
    
    # Handle stats: internal or external
    if norm_dataset in ('Internal', 'internal', 'INTERNAL'):  # Use stats from radiomics
        if verbose:
            hprint("Get stats from excel file", os.path.join(inputPath, radiomics_filename))
        
        if stratified == True:
            # Create an empty dataframe to store stratified statistics
            stats = pd.DataFrame()
            
            # Loop through each unique sub_Analysis value and compute stats
            unique_sub_analyses = radiomics['sub_Analysis'].unique()
            for value in unique_sub_analyses:
                if verbose:
                    print(f"Calculating stats for sub_Analysis = {value}", flush=True)
                
                # Get the subset for the current sub_Analysis value
                subset = radiomics[radiomics['sub_Analysis'] == value]
                subset_stats = subset[radiomics_columns].describe()
                
                # Add sub_Analysis identifier to the stats
                subset_stats['sub_Analysis'] = value
                stats = pd.concat([stats, subset_stats])
            
            # Also calculate overall stats for 'all'
            overall_stats = radiomics[radiomics_columns].describe()
            overall_stats['sub_Analysis'] = 'all'
            stats = pd.concat([stats, overall_stats])
        else:
            # Non-stratified: use overall stats for the whole dataset
            stats = radiomics[radiomics_columns].describe()
            stats['sub_Analysis'] = 'all'
    
    else:  # Use external stats file
        if verbose:
            print("Get stats from: ", os.path.join(modelpath, stats_filename), flush=True)
        try:
            stats = pd.read_excel(os.path.join(modelpath, stats_filename))
            stats = stats.set_index('statistics')
        except Exception as e:
            print(f"\033[31mERROR! reading statistics file {os.path.join(modelpath, stats_filename)}:\033[0m {e}", flush=True)
            return
    
    # Initialize the DataFrame to hold normalized data
    radiomics_norm = pd.DataFrame()
    
    # Handle stratified normalization if required
    if stratified == True:
        unique_sub_analyses = radiomics['sub_Analysis'].unique()
        
        for value in unique_sub_analyses:
            if verbose:
                print(f"Normalizing sub_Analysis = {value}", flush=True)
            
            # Filter radiomics for the current sub_Analysis group
            subset = radiomics[radiomics['sub_Analysis'] == value]
            
            # Filter stats for the current sub_Analysis group or use 'all' if not stratified
            if value in stats['sub_Analysis'].values:
                current_stats = stats[stats['sub_Analysis'] == value]
            else:
                current_stats = stats[stats['sub_Analysis'] == 'all']
            
            # Apply normalization for the subset using current_stats
            subset_norm = subset.copy()
            
            if method in ('MinMax', 'minmax', 'MINMAX', 'Min Max', 'min max', 'MIN MAX'):
                subset_norm[radiomics_columns] = subset[radiomics_columns].apply(lambda col: (col - current_stats[col.name]['min']) / (current_stats[col.name]['max'] - current_stats[col.name]['min']))
            
            elif method in ('Z-Score', 'ZScore', 'Z Score', 'z-score', 'zscore', 'z score'):
                subset_norm[radiomics_columns] = subset[radiomics_columns].apply(lambda col: (col - current_stats[col.name]['mean']) / current_stats[col.name]['std'])
            
            elif method in ('RobustScaling', 'Robust Scaling', 'robust scaling', 'Robust scaling'):
                subset_norm[radiomics_columns] = subset[radiomics_columns].apply(lambda col: (col - current_stats[col.name]['50%']) / (current_stats[col.name]['75%'] - current_stats[col.name]['25%']))
            
            else:
                print(f"\033[31mERROR! {method} is not a valid normalization method\033[0m", flush=True)
                sys.exit()
            
            # Append the normalized subset to the final DataFrame
            radiomics_norm = pd.concat([radiomics_norm, subset_norm], ignore_index=True)
    
    else:  # Non-stratified normalization (whole dataset)
        if verbose:
            print(f"Perform normalization (method: {method}, whole dataset)", flush=True)
        
        # Apply the chosen normalization method using 'all' stats from the stats file
        overall_stats = stats[stats['sub_Analysis'] == 'all']
        
        if method in ('MinMax', 'minmax', 'MINMAX', 'Min Max', 'min max', 'MIN MAX'):
            radiomics_norm = radiomics.copy()
            radiomics_norm[radiomics_columns] = radiomics[radiomics_columns].apply(lambda col: (col - overall_stats[col.name]['min']) / (overall_stats[col.name]['max'] - overall_stats[col.name]['min']))
        
        elif method in ('Z-Score', 'ZScore', 'Z Score', 'z-score', 'zscore', 'z score'):
            radiomics_norm = radiomics.copy()
            radiomics_norm[radiomics_columns] = radiomics[radiomics_columns].apply(lambda col: (col - overall_stats[col.name]['mean']) / overall_stats[col.name]['std'])
        
        elif method in ('RobustScaling', 'Robust Scaling', 'robust scaling', 'Robust scaling'):
            radiomics_norm = radiomics.copy()
            radiomics_norm[radiomics_columns] = radiomics[radiomics_columns].apply(lambda col: (col - overall_stats[col.name]['50%']) / (overall_stats[col.name]['75%'] - overall_stats[col.name]['25%']))
        
        else:
            print(f"\033[31mERROR! {method} is not a valid normalization method\033[0m", flush=True)
            sys.exit()
    
    # Save the normalized results
    if verbose:
        hprint("Saving normalized results in",os.path.join(outputPath, normalized_radiomics_filename))
    
    try:
        radiomics_norm.to_excel(os.path.join(outputPath, normalized_radiomics_filename), index=False)
    except Exception as e:
        print(f"\033[31mERROR:\033[0m{e}", flush=True)
        print(f"\033[31mERROR saving {os.path.join(outputPath, normalized_radiomics_filename)}\033[0m", flush=True)    



if __name__ == "__main__":
    main(sys.argv[1:])   
