#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Move or copy the input folder to the output folder

Usage: no_reorganize.py -i <inputfolder> -o <outputfolder>
Help: no_reorganize.py -h
"""

import sys, getopt
import shutil
from datetime import datetime
from utils import hprint_msg_box

def main(argv):
    inpath = ''
    outpath = ''
    log = ''
    new_log = False
    verbose = False
    cp = True
    try:
        opts, args = getopt.getopt(argv, "vhi:o:",["verbose","help","inFolder=","outFolder=","mv","log=","new_log"])
    except getopt.GetoptError:
        print('no_reorganize.py -i <inputfolder> -o <outputfolder>',flush=True)
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME",flush=True)
            print("\tno_reorganize.py\n",flush=True)
            print("SYNOPSIS",flush=True)
            print("\tno_reorganize.py [-h|--help][-v|--verbose][-i|--inFolder <inputfolder>][-o|--outFolder <outputfolder>][--mv]\n",flush=True)
            print("DESRIPTION",flush=True)
            print("\tMove or copy the input folder to the output folder\n",flush=True)
            print("OPTIONS",flush=True)
            print("\t -h, --help: print this help page",flush=True)
            print("\t -v, --verbose: False by default",flush=True)
            print("\t -i, --inFolder: input folder",flush=True)
            print("\t -o, --outFolder: output folder",flush=True)
            print("\t --mv, move folder instead of copy",flush=True)
            print("\t --log: redirect stdout to a log file",flush=True)
            print("\t --new_log: overwrite previous log file")
            sys.exit()
            
        elif opt in ("-i", "--inFolder"):
            inpath = arg
        elif opt in ("-o", "--outFolder"):
            outpath = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("--mv"):
            cp = False
        elif opt in ("--log"):
            log= arg
        elif opt in ("--new_log"):
            new_log= True
    
    if log != '':
        if new_log:
            f = open(log,'w+')
        else:
            f = open(log,'a+')
        sys.stdout = f 
    
    if verbose:
        msg = (
            f"Input folder: {inpath}\n"
            f"Output folder: {outpath}\n"
            f"Verbose: {verbose}\n"
            f"Log: {log}\n"
            f"Overwrite previous log file: {str(new_log)}\n"
            f"Copy mode: {cp}\n"
            )
        hprint_msg_box(msg=msg, indent=2, title=f"SKIP REORGANIZE {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    if cp:
        try:
            shutil.copytree(inpath,outpath)
            print(inpath, " was copied to ",outpath,flush=True)
        except:
            print("\033[31mERROR copying ", inpath, " to ",outpath,"\033[0m",flush=True)
    else:
        try:
            shutil.move(inpath,outpath)
            print(inpath, " was moved to ",outpath,flush=True)
        except:
            print("\033[31mERROR moving ", inpath, " to ",outpath,"\033[0m",flush=True)
                

if __name__ == "__main__":
    main(sys.argv[1:])         
