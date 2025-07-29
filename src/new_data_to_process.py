#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copy new data to a pool folder created in <outFolder>. Data copied are those created more than <delay> minutes ago and are not already present in the <patients_list> file.

Usage: new_data_to_process.py -i <inputfolder> -o <outputfolder>
Help: new_data_to_process.py -h
"""

import sys, getopt, os
import glob
from tqdm import tqdm
import time
import shutil
from datetime import datetime
import subprocess

def main(argv):
    img2radiomics_path=''
    inpath = ''
    outpath = ''
    log = ''
    force=False
    verbose = False
    remove_after_processing = False #remove data from the pool after processing
    cdelay = 0. #files need to be created more than <cdelay> (default: 0) min ago to be copied to the pool 
    tdelay = 1. #comparison of folder size after a delay of <tdelay> 
    patients_list = ''
    pool_name = 'pool_'+str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    new_pool = False #Set to true if a new pool is found
    job_scheduler='SLURM'
    script_submit_job_name='SLURM/sbatch_img2radiomics_auto.sh'
    
    try:
        opts, args = getopt.getopt(argv, "rvhi:o:fc:t:j:",["IMG2RADIOMICS=","verbose","help","patients_list=","inFolder=","outFolder=","tdelay=","cdelay=","log=","force","job_name=","remove","job_scheduler="])
    except getopt.GetoptError:
        print('new_data_to_process.py -i <inputfolder> -o <outputfolder>',flush=True)
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME",flush=True)
            print("\tnew_data_to_process.py\n",flush=True)
            print("SYNOPSIS",flush=True)
            print("\tnew_data_to_process.py [-h|--help][-v|--verbose][-i|--inFolder <inputfolder>][-o|--outFolder <outputfolder>][--patients_list <textfile>][--delay <timeInMinutes>]\n",flush=True)
            print("DESRIPTION",flush=True)
            print("\tCopy new data to a pool folder created in <outFolder>. Data copied are those created more than <cdelay> minutes ago, have a size that didn't change in the last <tdelay> seconds, and are not already present in the <patients_list> file\n",flush=True)
            print("OPTIONS",flush=True)
            print("\t -h, --help: print this help page",flush=True)
            print("\t --IMG2RADIOMICS: path where is img2radiomics is located",flush=True)
            print("\t -v, --verbose: False by default",flush=True)
            print("\t -i, --inFolder: input folder",flush=True)
            print("\t -o, --outFolder: output folder",flush=True)
            print("\t -c, --cdelay, only files created more than <cdelay> min ago are considered (default: 0 min)",flush=True)
            print("\t -t, --tdelay: only files with the same size between <tdelay> seconds are considered (default: 1 sec)",flush=True)
            print("\t --patients_list: only files not in the patient_list are considered (NOT IMPLEMENTED YET)",flush=True)
            print("\t -f, --force: copy patients even if they are already present in the patients_list (NOT IMPLEMENTED YET)",flush=True)
            print("\t -j, --job_name: name of the script to submit the job (default: SLURM/sbatch_img2radiomics_auto.sh)",flush=True)
            print("\t --job_scheduler: use SGE or SLURM to schedule jobs (default SLURM)",flush=True)
            print("\t -r --remove: remove data from the pool when finished processing",flush=True)
            print("\t --log: redirect stdout to a log file",flush=True)
            sys.exit()
            
        elif opt in ("-i", "--inFolder"):
            inpath = arg
        elif opt in ("-o", "--outFolder"):
            outpath = arg
        elif opt in ("--IMG2RADIOMICS"):
            img2radiomics_path = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-r", "--remove"):
            remove_after_processing = True
        elif opt in ("-f","--force"):
            force = True
        elif opt in ("--log"):
            log= arg 
        elif opt in ("-c","--cdelay"):
            cdelay = float(arg)
        elif opt in ("-t","--tdelay"):
            tdelay = float(arg)
        elif opt in ("--patients_list"):
            patients_list = arg
        elif opt in ("-j","--job_name"):
            script_submit_job_name = arg
        elif opt in ("--job_scheduler"):
            job_scheduler = arg   
   
    if log != '':
        f = open(log,'a+')
        sys.stdout = f
    
    if job_scheduler in ('SGE','Sge','sge'):
        try:
            with open(os.path.join(str(img2radiomics_path),"path_to_qsub.txt"),"r") as file:
                path_to_job_scheduler=file.read()
                file.close()
        except:
                sys.exit()
    elif job_scheduler in ('SLURM','Slurm','slurm'):
         try:
             with open(os.path.join(str(img2radiomics_path),"path_to_sbatch.txt"),"r") as file:
                 path_to_job_scheduler=file.read()
                 file.close()
         except:
                 sys.exit()
    elif job_scheduler in ('NONE','None','none'):
        path_to_job_scheduler=img2radiomics_path
    else:
        path_to_job_scheduler=''
        print("ERROR! Job scheduler ",job_scheduler," not found",flush=True)

        
    if verbose:
        print("-" * 50,flush=True)
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),flush=True)
        print("Input folder: "+inpath,flush=True)
        print("Output folder: "+outpath,flush=True)
        print("Patients list file: "+patients_list,flush=True)
        print("Use file created before "+str(cdelay),"min",flush=True)
        print("Use file with stable size during "+str(tdelay),"sec",flush=True)
        print("Force mode: "+str(force),flush=True)
        print("Name of the script to submit the job: "+str(script_submit_job_name),flush=True)
        print("Path to folder with job script: "+str(img2radiomics_path),flush=True)
        print("Path to job scheduler: "+str(path_to_job_scheduler),flush=True)
        print("Verbose: "+str(verbose),flush=True)
        print("log: ",str(log),flush=True)
    
    pool_path=os.path.join(outpath,pool_name)
    for patient in tqdm(glob.glob(inpath+"/*"),
                        ncols=100,
                        desc="Checking for new data:",
                        bar_format="{l_bar}{bar} [time left: {remaining}, time spent: {elapsed}]",
                        colour="yellow"):
        
        try:   # os.path.getmtime(patient) cannot be run is another instance of the program is using the folder => skip patient in the current instance
            time_patientID = os.path.getmtime(patient)
            if (time.time()-time_patientID)/60 > float(cdelay): #consider only file created more than <delay> min ago
                dif_time = 0
                if tdelay != 0:
                    try:
                        size_t0=int(subprocess.check_output(['du','-sb', patient]).split()[0])
                        time.sleep(tdelay)
                        size_t1=int(subprocess.check_output(['du','-sb', patient]).split()[0])
                        dif_time= size_t1-size_t0
                    except:
                        dif_time = 1 # if du -sb can fail if file is currently used
                        if verbose:
                            print("Skip patient: ",patient,flush=True)
                if dif_time == 0: #patient has finished copying OR tdelay not used
                    #add check DB to know if radiomics was already calculated for this patients (if force == False)
                    if not os.path.exists(pool_path):
                        os.makedirs(pool_path)       
                    try:
                        new_pool = True
                        shutil.move(patient,pool_path)
                    except:
                        print("ERROR! Data were not copied to the pool", flush=True)
            else:
                if verbose:
                    print("Skip patient: ",patient,flush=True)
        except:
            if verbose:
                print("Patient ",patient," already in used by another instance",flush=True)
    if new_pool == True:
        if verbose:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "- Process pool: ",pool_path,flush=True)
        run_pool(outpath,pool_name,path_to_job_scheduler,job_scheduler,img2radiomics_path,script_submit_job_name)
    else:
        if verbose:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "- No new data",flush=True)
    #read file with job ID and pool name
    if remove_after_processing: #remove pool for finished jobs
        remove(outpath,path_to_job_scheduler,job_scheduler)

def run_pool(outpath,pool_name,path_to_job_scheduler,job_scheduler,PATH,script_submit_job_name):
    pool_path=os.path.join(outpath,pool_name)
    inFolder = 'inFolder='+str(pool_path)
    if job_scheduler in ('SGE','Sge','sge'):
        prog=[path_to_job_scheduler+'qsub','-terse','-v',inFolder,PATH+script_submit_job_name]    
        print("QSUB: ", prog, flush=True)
        try:
            job_id=subprocess.check_output(prog)
            with open(os.path.join(outpath,"job_ids.txt"),'a+') as f:
                f.write(str(job_id.decode().strip())+'\t'+str(pool_name)+'\n')
        except:
            print("ERROR! ", script_submit_job_name)
    elif job_scheduler in ('SLURM','Slurm','slurm'):
        prog=[path_to_job_scheduler+'sbatch','--export',inFolder,PATH+script_submit_job_name]    
        print("SBATCH: ", prog, flush=True)
        try:
            job_id=subprocess.check_output(prog)
            with open(os.path.join(outpath,"job_ids.txt"),'a+') as f:
                f.write(str(job_id.decode().strip().split()[-1])+'\t'+str(pool_name)+'\n')
        except:
            print("ERROR! ", script_submit_job_name)
    elif job_scheduler in ('NONE','None','none'):
        prog=PATH+script_submit_job_name+' '+inFolder
        print("BATCH: ", prog, flush=True)
        try:
            job_id=subprocess.Popen(prog, shell=True)
            with open(os.path.join(outpath,"job_ids.txt"),'a+') as f:
                f.write(str(job_id.pid)+'\t'+str(pool_name)+'\n')
        except Exception as e:
            print(f"ERROR: {e}",flush=True)       
            print("ERROR! ", script_submit_job_name)
    else:
        print("ERROR! The job scheduler ",job_scheduler," is not available",flush=True) 

def remove(path,path_to_job_scheduler,job_scheduler):
    if job_scheduler in ('SGE','Sge','sge'):
        current_job_ids=subprocess.check_output(path_to_job_scheduler+"qstat | awk '{print $1}'",shell=True)
    elif job_scheduler in ('SLURM','Slurm','slurm'):
        current_job_ids=subprocess.check_output("squeue -u $(whoami) | awk '{print $1}'",shell=True)
    elif job_scheduler in ('NONE','None','none'):
        current_job_ids = subprocess.check_output("pgrep -u $(whoami)", shell=True)
    else:
        print("ERROR! The job scheduler ",job_scheduler," is not available",flush=True)
        current_job_ids=''

    list_current_job_ids=current_job_ids.decode().split('\n')
        
    try:    #job_ids.txt is created only after a pool was find
        with open(os.path.join(path,'job_ids.txt'),'r') as file, open(os.path.join(path,'.tmp_job_ids.txt'),'w') as tmp:
            for line in file:
                columns = line.strip().split('\t')
                try:
                    id_value = str(columns[0])
                    pool_name=columns[1]
                    if not id_value in list_current_job_ids:
                        folder_list=[f for f in os.listdir(path) if os.path.isdir(os.path.join(path,f))]
                        matching_folders= [folder for folder in folder_list if pool_name in folder]
                        for folder_to_remove in matching_folders:
                            shutil.rmtree(os.path.join(path,folder_to_remove))
                            print("Folder",folder_to_remove, "was deleted successfully", flush=True)
                        continue #not copy this line in tmp file
                    tmp.write(line)
                except:
                    print("ERROR! check job_ids.txt file", flush=True)
        os.rename(os.path.join(path,'.tmp_job_ids.txt'),os.path.join(path,'job_ids.txt'))
    except:
        sys.exit()
    
if __name__ == "__main__":
    main(sys.argv[1:])     
