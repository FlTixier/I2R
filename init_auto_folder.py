#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
initialization for  new_data_to_process.py

Usage: init_new_data_to_process.py
Help: init_new_data_to_process.py -h
"""


import sys, getopt, os
import subprocess

def main(argv):
    minutes=10
    cdelay=0
    tdelay=1
    folder=''
    workdir=''
    log=''
    job_scheduler='SLURM' 
    remove_after_processing = False
    script_submit_job_name='SLURM/sbatch_img2radiomics_auto.sh'

    try:
        opts, args = getopt.getopt(argv, "rhf:i:o:m:j:",["remove","help","log=","cdelay=","tdelay=","job_scheduler=","job_name="])
    except getopt.GetoptError:
        print('init_new_data_to_process.py -i <input folder> -o <working directory>',flush=True)
        sys.exit(2)
    for opt,arg in opts:
          if opt in ("-h", "--help"):
            print("NAME",flush=True)
            print("\tinit_new_data_to_process.py\n",flush=True)
            print("SYNOPSIS",flush=True)
            print("\tinit_new_data_to_process.py [-j <script with job to submit>][-h]\n",flush=True)
            print("DESRIPTION",flush=True)
            print("\tinitialization for  new_data_to_process.py\n",flush=True)
            print("OPTIONS",flush=True)
            print("\t -h: print this help page",flush=True)
            print("\t -m, new_data_to_process will be checked every <m> minutes (default 10 min)",flush=True)
            print("\t --cdelay, only folder created after <cdelay> min will be read (default: 0 min)",flush=True)
            print("\t --tdelay, only folder whith size staying stable during <tdelay> seconds will be read (default 1sec)" ,flush=True)
            print("\t -i, absolute path to the folder to check for new data -- WARNING: data put in this folder will be automatically deleted" ,flush=True)
            print("\t -o, absolute path to the working directory to process the data" ,flush=True)
            print("\t -r --remove, remove data from the pool when finished processing",flush=True)
            print("\t -j --job_name, name of the script to submit the job (default: qsub_img2radiomics_auto.sh",flush=True)
            print("\t --job_scheduler, use SGE or SLURM to schedule jobs (default SGE)",flush=True)
            print("\t --log, absolute path to the log file for crontab task" ,flush=True)
            sys.exit()
          elif opt in ("-i"):
              folder = arg
          elif opt in ("-o"):
              workdir = arg
          elif opt in ("-m"):
              minutes = int(arg)  
          elif opt in ("--log"):
              log= arg 
          elif opt in ("-c","--cdelay"):
              cdelay = float(arg)
          elif opt in ("-t","--tdelay"):
              tdelay = float(arg)  
          elif opt in ("-r", "--remove"):
              remove_after_processing = True   
          elif opt in ("--job_scheduler"):
              job_scheduler = arg
          elif opt in ("-j","--job_name"):
              script_submit_job_name = arg
        
    
    #HOME
    try:
        HOME=subprocess.check_output(['echo $HOME'],shell=True).decode().strip()
        print("HOME:",HOME,flush=True)
    except:
        print("ERROR! HOME not found",flush=True)
    #write path to job scheduler
    if job_scheduler in ('SGE','Sge','sge'):
        #write path to qsub
        try:
            f = open("path_to_qsub.txt","w")
            PATH_TO_QSUB=subprocess.check_output(['which','qsub']).decode().split('qsub')[0]
            f.write(PATH_TO_QSUB)
            f.close()
            print("PATH_TO_QSUB",PATH_TO_QSUB,flush=True)
        except:
            print("ERROR! Path to qsub not found, it can be added manually in the file 'path_to_qsub.txt'",flush=True)
    elif job_scheduler in ('SLURM','Slurm','slurm'):
        #write path to slurm
        try:
            f = open("path_to_sbatch.txt","w")
            PATH_TO_SLURM=subprocess.check_output(['which','sbatch']).decode().split('sbatch')[0]
            f.write(PATH_TO_SLURM)
            f.close()
            print("PATH_TO_SLURM",PATH_TO_SLURM,flush=True)
        except:
            print("ERROR! Path to sbatch not found, it can be added manually in the file 'path_to_sbatch.txt'",flush=True)
    elif job_scheduler in ('NONE','None','none'):
        pass
    else:
            print("ERROR! The job scheduler ",job_scheduler," is not available",flush=True)
    #write path to img2radiomics
    try:
        PATH_IMG2RADIOMICS=os.getcwd().replace('~',HOME)+'/'
        print("PATH_IMG2RADIOMICS",PATH_IMG2RADIOMICS,flush=True)
    except:
        print("ERROR! Path to img2radiomics, it can be added manually in the file 'path_to_img2radiomics.txt'",flush=True)
    #SGE_ROOT
    if job_scheduler in('SGE','Sge','sge'):
        try:
            SGE_ROOT=subprocess.check_output(['echo $SGE_ROOT'],shell=True).decode().strip()+'/'
            print("SGE_ROOT: ",SGE_ROOT,flush=True)
        except:
            print("ERROR! SGE_ROOT not found",flush=True)
    #python
    try:
        PYTHON=subprocess.check_output(['which','python3.11']).decode().strip().replace('~',HOME)
        print("PYTHON",PYTHON,flush=True)
    except:
        print("ERROR! Python 3.11 not found, trying to find another version",flush=True)
        try:
            PYTHON=subprocess.check_output(['which','python3']).decode().strip().replace('~',HOME)
            print("PYTHON",PYTHON,flush=True)
        except:
            print("ERROR! No version of python 3 found",flush=True)
    
    
    #add job in crontab
    if job_scheduler in ('SGE','Sge','sge'):
        try:    
            if remove_after_processing:
                cron='(crontab -l 2>/dev/null; echo "*/'+str(minutes)+' * * * * SGE_ROOT='+SGE_ROOT+' '+PYTHON+' '+PATH_IMG2RADIOMICS+'src/new_data_to_process.py -i '+folder+' -o '+workdir+' --IMG2RADIOMICS '+PATH_IMG2RADIOMICS+' -v -r --cdelay '+str(cdelay)+' --tdelay '+str(tdelay)+' --job_name '+ script_submit_job_name + ' --job_scheduler ' + job_scheduler + ' >> '+log+' 2>&1") | crontab -' 
            else:          
                cron='(crontab -l 2>/dev/null; echo "*/'+str(minutes)+' * * * * SGE_ROOT='+SGE_ROOT+' '+PYTHON+' '+PATH_IMG2RADIOMICS+'src/new_data_to_process.py -i '+folder+' -o '+workdir+' --IMG2RADIOMICS '+PATH_IMG2RADIOMICS+' -v --cdelay '+str(cdelay)+' --tdelay '+str(tdelay)+' --job_name '+ script_submit_job_name + ' --job_scheduler ' + job_scheduler + ' >> '+log+' 2>&1") | crontab -' 
            subprocess.call(cron,shell=True)
            print("CRONTAB: ",cron,flush=True)
        except:
            print("ERROR! Task was not added to crontab",flush=True)
    elif job_scheduler in ('SLURM','Slurm','slurm'):
        try:    
            if remove_after_processing:
                cron='(crontab -l 2>/dev/null; echo "*/'+str(minutes)+' * * * * '+PYTHON+' '+PATH_IMG2RADIOMICS+'src/new_data_to_process.py -i '+folder+' -o '+workdir+' --IMG2RADIOMICS '+PATH_IMG2RADIOMICS+' -v -r --cdelay '+str(cdelay)+' --tdelay '+str(tdelay)+' --job_name '+ script_submit_job_name + ' --job_scheduler ' + job_scheduler + ' >> '+log+' 2>&1") | crontab -' 
            else:          
                cron='(crontab -l 2>/dev/null; echo "*/'+str(minutes)+' * * * * '+PYTHON+' '+PATH_IMG2RADIOMICS+'src/new_data_to_process.py -i '+folder+' -o '+workdir+' --IMG2RADIOMICS '+PATH_IMG2RADIOMICS+' -v --cdelay '+str(cdelay)+' --tdelay '+str(tdelay)+' --job_name '+ script_submit_job_name + ' --job_scheduler ' + job_scheduler + ' >> '+log+' 2>&1") | crontab -' 
            subprocess.call(cron,shell=True)
            print("CRONTAB: ",cron,flush=True)
        except:
            print("ERROR! Task was not added to crontab",flush=True)
    elif job_scheduler in ('NONE','None','none'):
        try:    
            if remove_after_processing:
                cron='(crontab -l 2>/dev/null; echo "*/'+str(minutes)+' * * * * '+PYTHON+' '+PATH_IMG2RADIOMICS+'src/new_data_to_process.py -i '+folder+' -o '+workdir+' --IMG2RADIOMICS '+PATH_IMG2RADIOMICS+' -v -r --cdelay '+str(cdelay)+' --tdelay '+str(tdelay)+' --job_name '+ script_submit_job_name + ' --job_scheduler ' + job_scheduler + ' >> '+log+' 2>&1") | crontab -' 
            else:          
                cron='(crontab -l 2>/dev/null; echo "*/'+str(minutes)+' * * * * '+PYTHON+' '+PATH_IMG2RADIOMICS+'src/new_data_to_process.py -i '+folder+' -o '+workdir+' --IMG2RADIOMICS '+PATH_IMG2RADIOMICS+' -v --cdelay '+str(cdelay)+' --tdelay '+str(tdelay)+' --job_name '+ script_submit_job_name + ' --job_scheduler ' + job_scheduler + ' >> '+log+' 2>&1") | crontab -' 
            subprocess.call(cron,shell=True)
            print("CRONTAB: ",cron,flush=True)
        except:
            print("ERROR! Task was not added to crontab",flush=True)
    else:
        print("ERROR! The job scheduler ",job_scheduler," is not available",flush=True)

if __name__ == "__main__":
    main(sys.argv[1:])  
