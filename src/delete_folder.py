#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _DELETE:

The DELETE module allows for the deletion of a specified folder. This module is useful for removing folders created by previous modules that are no longer required for further processing.

.. warning::

    Specified folders will be deleted regardless of whether the module execution was successful. You can specify any folder in this module, even if it is not part of img2radiomics. **Please exercise caution when using this option.**

The DELETE module can be used with the following options:

- ``verbose``: Enable or disable verbose mode.

- ``timer``: Enable or disable the timer to record execution time.

- ``log``: Specify the path to a file for saving logs.

- ``folder``: Specify the path to the folder to be deleted.

Here is an example of how to use the DELETE module:

.. code-block:: bash

    DELETE:
    {
        folder: /path/to/NIFTI_folder  # Deletes NIFTI_folder, e.g., after creating NIFTI_RESAMPLED_folder with the RESAMPLING module
        log: /path/to/logs/delete.log
    }
"""

# delete_folder.py
# Delete a specified folder.
#
# Usage:
#     delete_folder.py -f <folder>
#
# Options:
#     -h, --help                   Show this help message and exit
#     -v, --verbose                Enable verbose output (default: False)
#     -f <folder>                  Specify the folder to delete
#     --log <logfile>              Redirect stdout to a log file (optional)
#
# Help:
#     delete_folder.py -h

import sys, getopt
import shutil

def main(argv):   
    path = ''
    verbose = False
    log = ''
    
    try:
        opts, args = getopt.getopt(argv, "f:vh",["log=","help","verbose"])
    except getopt.GetoptError:
        print('delete_folder.py -f <folder>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tdelete_folder.py\n")
            print("SYNOPSIS")
            print("\tdelete_folder.py [-h|--help][-v|--verbose][-f <folder>]\n")
            print("DESRIPTION")
            print("\tDelete folder")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -f, folder to delete")
            sys.exit()
        elif opt in ("-f"):
            path = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--log"):
            log= arg 

    if log != '':
        f = open(log,'a+')
        sys.stdout = f
    
    if verbose:
           print("Folder to delete: "+path,flush=True)
           
    try:
        delete_folder(path)
        print("Folder "+path+" was deleted",flush=True)
    except:
        print("ERROR The folder "+path+" was not corectly deleted", flush=True)
        

def delete_folder(path):
   shutil.rmtree(path)
        

if __name__ == "__main__":
    main(sys.argv[1:])
