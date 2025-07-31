#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_testing_pipeline_file allows to generate a testing pipeline file to apply a model on new data (testing sets or prospective studies)

Usage: gen_testing_pipeline_file.py -r <referenceFolder>
Help: gen_testing_pipeline_file.py -h
"""

import os,sys, getopt
import readline
import pandas as pd

def main(argv):
    referenceFolder = ''   
    newInputFolderStrategy = 'manual'
    predictModule=False
    log_suffix='testing'
    
    try:
        opts, args = getopt.getopt(argv, "hr:s:p",["help","referenceFolder=","strategy=","suffix="])
    except getopt.GetoptError:
        print('gen_testing_pipeline_file.py -m <referenceFolder>', flush=True)
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME", flush=True)
            print("\tgen_testing_pipeline_file.py\n", flush=True)
            print("SYNOPSIS", flush=True)
            print("\tgen_testing_pipeline.py [-h|--help][-m|--referenceFolder <referenceFolder>]\n", flush=True)
            print("DESRIPTION", flush=True)
            print("\tgen_testing_pipeline_file allows to generate a testing pipeline file to apply a model on new data (testing sets or prospective studies)\n", flush=True)
            print("OPTIONS", flush=True)
            print("\t -h, --help: print this help page", flush=True)
            print("\t -r, --referenceFolder: Folder with a PIPELINE file and radiomics files used for training", flush=True)
            print("\t -s, --strategy: Strategy to define new input folder path: \n\t\t'manual': prompt path for all new input folder for all the modules, \n\t\t'suffix': prompt first new input folder and use outputFolderSuffix for the other input folders, \n\t\t'auto': use '.' and 'PREVIOUS_BLOCK_OUTPUT_FOLDER' as new input folder", flush=True)
            print("\t -p: Add PREDICT module in the testing pipeline file", flush=True)
            print("\t --suffix: suffix to use in the new log files (default: 'testing')", flush=True)

            sys.exit()
        elif opt in ("-r", "--referenceFolder"):
            referenceFolder = arg
        elif opt in ("-s","--strategy"):
            newInputFolderStrategy = arg
        elif opt in ("-p"):
            predictModule = True
        elif opt in ("--suffix"):
             log_suffix = arg

    if not referenceFolder:
        print("\033[31mError: Missing reference folder. Use -r or --referenceFolder to specify the path to the reference folder.\033[0m",flush=True)
        sys.exit(2)
    
    if not os.path.isfile(referenceFolder):
        print(f"\033[31mError: Reference folder '{referenceFolder}' not found.\033[0m",flush=True)
        sys.exit(2)        

    #Check input folder strategy    
    if not newInputFolderStrategy in ('manual','suffix','auto'):
            print_red("Incorrect strategy for defining a new input folder path")
            print("You will be prompted to specify a new input folder path for all the modules", flush=True)
            newInputFolderStrategy = 'manual'
    
    #prompt for pipeline file    
    prompt="\033[92mSelect the PIPELINE file that was used to extract radiomics from the training set (Enter '0' to quit): \033[0m"
    pipeline_file=selectFile(modelFolder,prompt)

    
    try:
        files = os.listdir(modelFolder)
    except Exception as e:
        print(f"ERROR:{e}",flush=True)
         
    #prompt new pipeline file name
    while True:
       try:
           choice = input("\033[92mName of the new pipeline file for testing set: \033[0m")
           if choice in files:
               print_red("file already exist in "+modelFolder+", please enter a different name")
           else:
               pipeline_file_testing=choice
               print(f"New Pipeline file: \033[93m{pipeline_file_testing}\033[0m")
               break
       except ValueError:
               print_red("Invalid input. Please enter a valid file name")

    create_testing_pipeline_file(os.path.join(modelFolder,pipeline_file),os.path.join(modelFolder,pipeline_file_testing),newInputFolderStrategy,modelFolder,predictModule,log_suffix)
             

def create_testing_pipeline_file(pipeline_file,pipeline_file_testing,strategy,modelFolder,predictModule,log_suffix):
    config=''
    newInputFolder=''
    resultFolder=''
    with open(pipeline_file, 'r') as infile:
        with open(pipeline_file_testing, 'w') as outfile:         
            line="#TESTING PIPELINE FILE GENERATED WITH gen_testing_pipeline_file.py\n"
            outfile.write(line)
            for raw_line in infile:
                line=raw_line.strip()
                if not line: #empty line
                    outfile.write(raw_line)
                elif line[0] == '#':  #comment lines
                    outfile.write(raw_line)                 
                
                elif 'GLOBAL_PARAMETERS' in line.split('#')[0] or config == 'GLOBAL_PARAMETERS':
                    config= 'GLOBAL_PARAMETERS'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of GLOBAL_PARAMETERS
                    else:
                        outfile.write(raw_line)
                
                elif 'CHECK_FOLDER' in line.split('#')[0] or config == 'CHECK_FOLDER':
                    config= 'CHECK_FOLDER'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of CHECK_FOLDER
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:
                            suffix="None"
                            promptIn="Enter the input path to use for the testing set (module CHECK_FOLDER):"
                            promptOut=""
                            if strategy == 'auto': #no update of newInputFolder for CHECK_FOLDER. To avoid input folder set as PREVIOUS_BLOCK_OUTPUT_FOLDER in reorganize module
                                line_in,line_out,_=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut) 
                            else:
                                line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut) 
                            outfile.write(line_in)
                            if line_out != '':outfile.write(line_out)
                        else:
                            outfile.write(raw_line)

                elif 'REORGANIZE' in line.split('#')[0] or config == 'REORGANIZE':
                    config= 'REORGANIZE'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of REORGANIZE
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:    
                            suffix="ready"
                            promptIn="Enter the input path to use for the testing set (module REORGANIZE):"
                            promptOut="Enter the output path to use for the testing set (module REORGANIZE):"
                            line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut)
                            outfile.write(line_in)
                            if line_out != '':outfile.write(line_out)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix']):  #skip line
                             continue
                        else:
                            outfile.write(raw_line)                

                elif 'DCM2NII' in line.split('#')[0] or config == 'DCM2NII':
                    config= 'DCM2NII'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of DCM2NII
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:    
                            suffix="nii"
                            promptIn="Enter the input path to use for the testing set (module DCM2NII):"
                            promptOut="Enter the output path to use for the testing set (module DCM2NII):"
                            line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut)
                            outfile.write(line_in)
                            if line_out != '':outfile.write(line_out)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','skip']):  #skip line
                             continue
                        else:
                            outfile.write(raw_line)                

                elif 'RESAMPLING' in line.split('#')[0] or config == 'RESAMPLING':
                    config= 'RESAMPLING'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of RESAMPLING
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:    
                            suffix="resampled"
                            promptIn="Enter the input path to use for the testing set (module RESAMPLING):"
                            promptOut="Enter the output path to use for the testing set (module RESAMPLING):"
                            line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut)
                            outfile.write(line_in)
                            if line_out != '':outfile.write(line_out)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','skip']):  #skip line
                             continue
                        else:
                            outfile.write(raw_line)      
                
                elif 'MERGE_MASKS' in line.split('#')[0] or config == 'MERGE_MASKS':
                    config= 'MERGE_MASKS'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of MERGE_MASKS
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:    
                            suffix="None"
                            promptIn="Enter the input path to use for the testing set (module MERGE_MASKS):"
                            promptOut="Enter the output path to use for the testing set (module MERGE_MASKS):"
                            line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut)
                            outfile.write(line_in)
                            if line_out != '':outfile.write(line_out)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','skip']):  #skip line
                             continue
                        else:
                            outfile.write(raw_line)      

                elif 'MASK_THRESHOLDING' in line.split('#')[0] or config == 'MASK_THRESHOLDING':
                    config= 'MASK_THRESHOLDING'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of MASK_THRESHOLDING
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:    
                            suffix="None"
                            promptIn="Enter the input path to use for the testing set (module MASK_THRESHOLDING):"
                            promptOut="Enter the output path to use for the testing set (module MASK_THRESHOLDING):"
                            line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut)
                            outfile.write(line_in)
                            if line_out != '':outfile.write(line_out)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','skip']):  #skip line
                             continue
                        else:
                            outfile.write(raw_line)      
 
                elif 'I-WINDOWING' in line.split('#')[0] or config == 'I-WINDOWING':
                    config= 'I-WINDOWING'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of I-WINDOWING
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:    
                            suffix="None"
                            promptIn="Enter the input path to use for the testing set (module MASK_THRESHOLDING):"
                            promptOut="Enter the output path to use for the testing set (module MASK_THRESHOLDING):"
                            line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut)
                            outfile.write(line_in)
                            if line_out != '':outfile.write(line_out)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','skip']):  #skip line
                             continue
                        else:
                            outfile.write(raw_line)   

                elif 'RADIOMICS' in line.split('#')[0] or config == 'RADIOMICS':
                    config= 'RADIOMICS'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of RADIOMICS
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:   
                            prompt="Enter the path to use for saving new results (module RADIOMICS):"
                            line_in,line_out,resultFolder=newResultFolderName(newInputFolder,prompt)
                            outfile.write(line_in)
                            outfile.write(line_out)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','skip']):  #skip line
                            continue
                        else:
                            outfile.write(raw_line)     

                elif 'DELETE' in line.split('#')[0] or config == 'DELETE': #skip DELETE Module
                    config= 'DELETE'
                    if line[0]=='}':
                        continue
                        config= '' #end of DELETE
                    else:
                       continue

                elif 'SEGMENTATION' in line.split('#')[0] or config == 'SEGMENTATION':
                    config= 'SEGMENTATION'
                    if line[0]=='}':
                        outfile.write(raw_line)
                        config= '' #end of SEGMENTATION
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:   
                            suffix="None"
                            promptIn="Enter the input path to use for the testing set (module SEGMENTATION):"
                            promptOut=''
                            line_in,line_out,newInputFolder=newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut)
                            outfile.write(line_in)
                        elif any(key in line.split()[0] for key in ['skip']):  #skip line
                            continue
                        else:
                            outfile.write(raw_line)    

                elif 'F-NORMALIZE' in line.split('#')[0] or config == 'F-NORMALIZE':
                    config= 'F-NORMALIZE'
                    if line[0]=='}':
                        outfile.write('\tmodelFolder: '+ modelFolder+'\n')
                        prompt="\033[92mSelect the Excel file that contains statistics on radiomics features used for the training set (0 to quit): \033[0m"
                        selected_file=selectFile(modelFolder,prompt)
                        outfile.write('\tstats_filename: '+ selected_file+'\n')
                        outfile.write('\tmode: External\n')
                        outfile.write(raw_line) #copy '}'
                        config= '' #end of F-NORMALIZE
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:   
                            line=selectResultFolder(resultFolder)
                            outfile.write(line)
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','mode', 'stats_filename']):  #skip line
                            continue
                        else:
                            outfile.write(raw_line)    
        
                elif 'F-HARMONIZE' in line.split('#')[0] or config == 'F-HARMONIZE':
                    config= 'F-HARMONIZE'
                    if line[0]=='}':
                        outfile.write('\tmodelFolder: '+ modelFolder+'\n')
                        prompt="\033[92mSelect the Excel file that contains radiomics features used for the training set (0 to quit): \033[0m"
                        selected_file=selectFile(modelFolder,prompt)
                        outfile.write('\tradiomics_from_model_filename: '+ selected_file+'\n')
                        prompt="\033[92mSelect the Excel file that contains batch information for the patients in the training set (0 to quit): \033[0m"
                        selected_file=selectFile(modelFolder,prompt)
                        outfile.write('\tbatch_from_model_filename: '+ selected_file+'\n')
                        outfile.write('\tmode: External\n')
                        outfile.write(raw_line) #copy '}'
                        config= '' #end of F-NORMALIZE
                    else:
                        if 'log'in line.split()[0]:
                            outfile.write(new_log(line,log_suffix))
                        elif 'inputFolder' in line.split()[0]:   
                            line=selectResultFolder(resultFolder)
                            outfile.write(line)
                        elif 'batch_file' in line.split()[0]:
                            new_batch_file=prompt_path("Enter excel file with batch information for the testing set: ")
                            outfile.write('\t'+line.split()[0]+' '+new_batch_file+'\n')
                        elif any(key in line.split()[0] for key in ['outputFolder','outputFolderSuffix','mode']):  #skip line
                            continue
                        else:
                            outfile.write(raw_line)   
                            
                else:
                    print("ERROR:"+ line.split('#')[0] +" not recognized",flush=True)
                    sys.exit()
                
            #Add 'PREDICT' module
            if predictModule:
                outfile.write('\nPREDICT:\n')
                outfile.write('{\n')
                outfile.write(selectResultFolder(resultFolder))
                outfile.write('\tmodelFolder: '+ modelFolder+'\n')
                prompt="\033[92mSelect the pickle file (.pkl) that contains the radiomics model to apply to the testing set (0 to quit): \033[0m"
                selected_file=selectFile(modelFolder,prompt)
                outfile.write('\tmodel_filename: '+ selected_file+'\n')
                outfile.write('\tpredict_filename: model_prediction.xlsx\n')
                outfile.write('\tlog: log_model_prediction.out\n')
                outfile.write('}\n\n')

            print_orange("New PIPLELINE file has been successfully created ("+pipeline_file_testing+")")





#prompt for new folder name and return pipeline line for InputFolder, OutputFolder and newInputFolder name
def newFolderName(strategy,newInputFolder,suffix,promptIn, promptOut):
    line_in = ''
    line_out = ''
    if strategy == 'manual':
        new_path_in=prompt_path(promptIn)
        new_path_out=prompt_path(promptOut)
        line_in='\tinputFolder: ' + new_path_in + '\n'
        if new_path_out != '': line_out = '\toutputFolder: ' + new_path_out + '\n'
    elif strategy == 'suffix':
        if newInputFolder == '':
            new_path_in=prompt_path(promptIn)
            line_in='\tinputFolder: ' + new_path_in + '\n'
            if suffix != "None": #don't write outputFolder line
                newInputFolder = new_path_in.rstrip('/')+"_"+suffix
                line_out = '\toutputFolderSuffix: ' + suffix + '\n'
            else:
                newInputFolder=new_path_in
        else:
            if suffix == "None": #don't write outputFolder line
                line_in='\tinputFolder: ' + newInputFolder + '\n'
            else :
                line_in='\tinputFolder: ' + newInputFolder + '\n'
                newInputFolder = newInputFolder.rstrip('/')+"_"+suffix
                line_out = '\toutputFolderSuffix: ' + suffix + '\n'
    elif strategy == 'auto':
        if newInputFolder == '':
            new_path_in='.'
            newInputFolder=new_path_in
            line_in='\tinputFolder: ' + new_path_in + '\n'
            if suffix != "None": line_out = '\toutputFolderSuffix: ' + suffix + '\n'
        else:
            new_path_in='PREVIOUS_BLOCK_OUTPUT_FOLDER'
            newInputFolder=new_path_in
            line_in='\tinputFolder: ' + new_path_in + '\n'
            if suffix != "None": line_out = '\toutputFolderSuffix: ' + suffix + '\n'
    else:
        print("ERROR, unrecognized strategy\n")
        sys.exit()
    return [line_in, line_out, newInputFolder]


#prompt for new result folder name and return pipeline line for InputFolder, OutputFolder and newResultFolder name
def newResultFolderName(newInputFolder,prompt):
    line_in= '\tinputFolder: ' + newInputFolder + '\n'
    new_path_out=prompt_path(prompt)
    line_out= '\toutputFolder: ' + new_path_out + '\n'
    return [line_in,line_out,new_path_out]


def selectResultFolder(resultFolder):
    return '\tinputFolder: ' + resultFolder + '\n'


def selectFile(path,prompt):
    try:
        files = os.listdir(path)
    except Exception as e:
        print(f"ERROR:{e}",flush=True)     
    print_green("Scanning files in the model folder "+path+"...") 
    for i,file in enumerate(files,start=1):
        print(f"{i}.{file}")
    while True:
       try:
           choice = int(input(prompt))
           if choice == 0:
               sys.exit(2)
           elif 1 <=choice <= len(files):
               selected_file= files[choice - 1]
               print(f"Selected file: \033[93m{selected_file}\033[0m")
               break
           else:
               print_red("Invalid input. Please enter a valid file number (0 to quit)")
       except ValueError:
               print_red("Invalid input. Please enter a valid file number (0 to quit)")
    return selected_file


def prompt_path(prompt="Enter a path: "):
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete") 
    path=input(prompt)
    return path

def new_log(line,suffix):
    directory,filename = os.path.split(line.split()[1])
    root,extension = os.path.splitext(filename)
    new_path = os.path.join(directory, root + "_" + suffix + extension)
    return '\t' + line.split()[0] + ' ' + new_path + '\n'
                   
def print_green(text):
    print("\033[92m"+ text + "\033[0m")           

def print_orange(text):
    print("\033[93m"+ text + "\033[0m")    

def print_red(text):
    print("\033[91m"+ text + "\033[0m")   

if __name__ == "__main__":
    main(sys.argv[1:])      
    
