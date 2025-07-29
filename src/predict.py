#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _PREDICT:

The PREDICT module enables making predictions on new data using a model previously built with the `sklearn` package and saved as a pickle file.

Here is an example of how to save a model as a pickle file:

.. code-block:: python

    from sklearn import svm
    from sklearn import datasets
    import joblib
    
    iris = datasets.load_iris()
    X, y = iris.data, iris.target
    
    clf = svm.SVC()
    clf.fit(X, y)
    
    joblib.dump(clf, "model.pkl")

The PREDICT module can be used with the following options:

- ``verbose``: Enable or disable verbose mode.
- ``timer``: Enable or disable the timer to record execution time.
- ``log``: Specify the path to a file for saving logs.
- ``new_log_file``: Create a new log file: if a log file with the same name already exists, it will be overwritten.
- ``inputFolder``: Specify the path to the input folder.
- ``outputFolder``: Specify the path to the output folder.
- ``modelFolder``: Specify the path with data from a previously built model (optional, to use with mode: `External`)
- ``radiomics_filename``: Specify the name of the Excel file with the radiomics results.
- ``model_filename``: Specify the name of the pickle file with the model.
- ``predict_filename``: Specify the name of the Excel file where predictions will be saved.

Here is an example of how to use the PREDICT module:

.. code-block:: bash

    PREDICT
    {
        inputFolder: /path/to/radiomics_results
        # No output folder specified: save output in the input folder
        modelFolder: /path/to/radiomics_model
        radiomics_filename: radiomics.xlsx
        model_filename: model.pkl
        predict_filename: predict.xlsx
        log: /path/to/logs/predict.log
    }

In this example:

- **inputFolder**: Specifies the folder containing radiomics results for prediction.
- **modelFolder**: Specifies the folder containing the pre-trained model.
- **radiomics_filename**: Specifies the Excel file containing the radiomics features for prediction.
- **model_filename**: Specifies the pickle file containing the saved model.
- **predict_filename**: Specifies the Excel file where predictions will be saved.
- **log**: Specifies a path for the log file.

"""

# Make predictions on new data using a pre-trained sklearn model.
# 
# Usage:
#     predict.py -i <inputFolder> --radiomicsFile <radiomics excel file> -m <modelFolder> --modelFile <model.pkl>
# 
# Options:
#     -h, --help                       Show this help message and exit
#     -v, --verbose                    Enable verbose output (default: False)
#     -i, --inputFolder <inputFolder>  Input folder containing radiomics features
#     -o, --outputFolder <outputFolder> Output folder to save prediction results
#     -m, --modelFolder <modelFolder>  Folder containing the saved model file (default: model.pkl)
#     -r, --radiomicsFile <radiomicsFile> Name of the Excel file with radiomics data to predict
#     -p, --predictFile <predictFile>  Name of the Excel file to save predictions (default: predicted.xlsx)
#     -M, --modelFile <modelFile>      Name of the pickle file with the sklearn model
#     --log <logFile>                  Redirect stdout to a log file
#     --new_log                        Overwrite previous log file if it exists
#
# Help:
#     predict.py -h

import sys, getopt, os
import joblib
import pandas as pd
from datetime import datetime
from utils import hprint_msg_box

def main(argv):
    modelpath = ''
    inpath = ''
    outpath = ''
    radiomics_filename = 'radiomics.xlsx'
    model_filename = 'model.pkl'
    prediction_filename='predicted.xlsx'
    verbose = False
    log = ''
    new_log = False

    try:
        opts, args = getopt.getopt(argv, "vhi:o:m:M:r:p:",["log=","new_log","verbose","help","radiomicsFile=","predictFile=","modelFile=","inputFolder=","outFolder=","modelFolder="])
    except getopt.GetoptError:
        print('predict.py -i <inputFolder> --radiomicsFile <radiomics excel file> -m <modelFolder> --modelFile <model.pkl>')
        sys.exit(2)
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print("NAME")
            print("\tpredict.py\n")
            print("SYNOPSIS")
            print("\predict.py [-h|--help][-v|--verbose][--log <logFile>][-i|--inputFolder <inputfolder>][-o|--outputFolder <outputFolder>][-r|--radiomicsFile <radiomicsFile>]\n")
            print("DESRIPTION")
            print("\tMake prediction on new data\n")
            print("OPTIONS")
            print("\t -h, --help: print this help page")
            print("\t -v, --verbose: False by default")
            print("\t -i, --inputFolder: input folder with radiomics and batch file")
            print("\t -o, --outFolder: output folder to save radiomics harmonization results")
            print("\t -m, --modelFolder: folder with model results (to be use with mode='writeEstimates_newData' or 'readEstimates')")
            print("\t -r, --radiomicsFile: name of the excel file with radiomics results")
            print("\t -p, --predictFile: name of the excel file to save prediction")
            print("\t -M, --modelFile: name of the pickel file with sklearn model to apply to new data")
            print("\t --log: redirect stdout to a log file")
            print("\t --new_log: overwrite previous log file", flush=True)
            sys.exit()
        elif opt in ("-i", "--inputFolder"):
            inpath = arg
        elif opt in ("-o", "--outputFolder"):
            outpath = arg
        elif opt in ("-m", "--modelFolder"):
            modelpath = arg
        elif opt in ("-r", "--radiomicsFile"):
            radiomics_filename = arg
        elif opt in ("-p", "--predictFile"):
            prediction_filename = arg  
        elif opt in ("-M", "--modelFile"):
            model_filename = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
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

    if outpath == '':
        outpath = inpath
     
        
    if verbose:
        msg = (
        f"Input folder: {inpath}\n"
        f"Output folder: {outpath}\n"
        f"Model folder: {modelpath}\n"
        f"Radiomics file: {radiomics_filename}\n"
        f"Model file: {model_filename}\n"
        f"Prediction file: {prediction_filename}\n"
        f"Verbose: {verbose}\n"
        f"Overwrite previous log file: {str(new_log)}\n"
        f"Log: {log}\n"
        )

        hprint_msg_box(msg=msg, indent=2, title=f"PREDICT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")   

    #IMPORT MODEL
    if verbose:
        print("Import model",os.path.join(modelpath,model_filename),flush=True)
    try:
        #IMPORT MODEL that have been saved using the following command:
            #model.fit(X,y)
            #joblib.dump(model,"model.pkl")
        model=joblib.load(os.path.join(modelpath,model_filename))
    except Exception as e:
        print(f"\033[31mERROR:\033[0m{e}",flush=True)

    #IMPORT RADIOMICS
    if verbose:
        print("Import radiomics",os.path.join(inpath,radiomics_filename),flush=True)
    try:
        df = pd.read_excel(os.path.join(inpath,radiomics_filename))
    except Exception as e:
        print(f"\033[31mERROR:\033[0m{e}",flush=True)
        
    #SELECT RADIOMICS FEATURES
    try:
        df_selected=df[model.feature_names_in_]         #sklearn model
    except:
        try:
            df_selected=df[model.feature_name()]        #lightGBM
        except Exception as e:
            print(f"\033[31mERROR:\033[0m{e}",flush=True)
       
    #MAKE PREDICTION
    if verbose:
        print("Apply model on new data",flush=True)
    try:
        pred=model.predict(df_selected)
    except Exception as e:
        print(f"\033[31mERROR:\033[0m{e}",flush=True)
    
    #SAVE PREDICTION
    if verbose:
        print("Save prediction in",os.path.join(outpath,prediction_filename),flush=True)
    try:
        pd.concat([df[['patientID','sub_Analysis']],pd.DataFrame(pred, columns=['predictions'])],axis=1).to_excel(os.path.join(outpath,prediction_filename),index=False)
    except Exception as e:
        print(f"\033[31mERROR:{e}\033[0m",flush=True)
        

if __name__ == "__main__":
    main(sys.argv[1:])   
