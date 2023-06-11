This repository has tools for batch extraction of features from UKBioBank MRIs in the Ritter lab server,
as well as command line tools for extracting features from individual brains. 

# -OPTIONAL: Clean Installation, Likely Only Necessary if One Had Package Version Problems- 
1. First navigate to the directory you imported code into. Create a new Anaconda environment with python 3.9 to house the project with the right versions of software.
   > conda create --name extract --file requirements.txt

2. Run `export PYTHONPATH=$PYTHONPATH:.`

# -Running BIDS feature extraction-

To extract features from the UkBioBank data folders, one must 

3. fill in the config file with their desired output destination and other variables. Explanations of each variable are included in the config file.
4. run batch_feature_extraction.py with nohup, which allows the user's code to continue running even after they have logged out of the cluster.
   >nohup python feature_extraction/batch_feature_extraction.py 
   
Note: One can let most features be default and only specify their output folder and number of mris with the command line. For example:
   >python feature_extraction/batch_feature_extraction.py --n_mris 10 --output_directory my/output/directory

   
