#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _COPY:

The COPY module allows copying the contents from one folder to another. For example, this module could be used to save automatic segmentations obtained for new cases using a deployed model.

The COPY module can be used with the following options:

- ``verbose``: Enable or disable verbose mode.

- ``timer``: Enable or disable the timer to record execution time.

- ``log``: Specify the path to a file for saving logs.

- ``inputFolder``: Specify the path to the input folder.

- ``targetFolder``: Specify the path to the output folder.

This module utilizes the `targetFolder` option instead of `outputFolder` to enable the `PREVIOUS_BLOCK_OUTPUT_FOLDER` option, disregarding the `outputFolder` used in the COPY module.

Here is an example of how to use the COPY module:

.. code-block:: bash

    COPY
    {
        inputFolder: /path/to/folder
        targetFolder: /path/to/target/folder
    }
"""

# Copy content from the input folder to the output folder.
#
# Usage:
#     copy_folder_content.py -i <inputFolder> -o <outputFolder>
# 
# Options:
#   -h, --help                     Show this help message and exit
#   -v, --verbose                  Enable verbose output (default: False)
#   -i, --inputFolder <inputFolder> Specify the path to the input folder
#   -o, --outputFolder <outputFolder> Specify the path to the output folder
#       --log <log file path>      Redirect stdout to a log file
#
# Help:
#     copy_folder_content.py -h

import sys, getopt
from datetime import datetime
from distutils.dir_util import copy_tree

def main(argv):
    inpath = ''
    outpath = ''
    verbose = False
    log = ''
    
    try:
        opts, args = getopt.getopt(argv, "vhi:o:",["log=","inputFolder=","outputFolder=","verbose","help"])
    except getopt.GetoptError:
        print('copy_folder_content.py -i <inputFolder> -o <inputFolder>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tcopy_folder_content.py\n")
            print("SYNOPSIS")
            print("\tcopy_folder_content.py[-h|--help][-v|--verbose][--log <logFile>][-i|--inputFolder <inputfolder>][-o|--outputFolder <outputFolder]\n")
            print("DESRIPTION")
            print("\tCopy input folder content to output folder\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder")
            print("\t -o, --outFolder: output folder")
            print("\t --log: stdout redirect to log file")
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--log"):
            log= arg
            

    if log != '':
         f = open(log,'a+')
         sys.stdout = f
        
    if verbose:
        print("-" * 50,flush=True)
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),flush=True)     
        print("Input folder: "+inpath,flush=True)
        print("Output folder: "+outpath,flush=True)
        print("Verbose "+str(verbose),flush=True)
        print("log:",str(log),flush=True)
        
        
    if inpath == '' or outpath == '':
        print("ERROR! input and output folders need to be specify",flush=True)
        sys.exit()
    elif inpath == outpath:
            print("ERROR! input and output path must be different",flush=True)
            sys.exit()
    else:
        print("before copying",flush=True)
        copy_tree(inpath,outpath)
        if verbose:
            print(inpath, "was copied to ", outpath, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
