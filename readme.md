Readme Outline
=============================
This repository has tools for batch extraction of features from UKBioBank MRIs in the Ritter lab server,
as well as command line tools for extracting features from individual brains. 
You can jump to the following sections of this readme:

- [Readme Outline](#readme-outline)
- [Functionality](#functionality)
- [Running BIDS feature extraction](#running-bids-feature-extraction)
  - [Clean Install](#optional-clean-installation)
  - [Command Line Options](#command-line-options)
- [Package File Structure](#package-file-structureorganization)
- [Full List of Extracted Variables](#full-list-of-extracted-variables)
  - [Graph Features](#graph-features)
  - [Correlation Features](#correlation-features)
  - [Brainnetome Features](#brainnetome-features)
  - [ICA Features](#ica-features)
- [Methods Appendix](#methods-appendix)
  - [On Inverse Transforms](#on-inverse-transforms)
  - [On Graph Splitting](#on-graph-splitting)
----------------------------------
# Functionality
At the heart of this package are two ideas for features. 
The first is to calculate graph network features of the brain, like small-worldedness. A graph is built 
by having regions of the brain represent nodes and taking highly correlated brain regions as deserving an edge between them.
Other features like path length and clustering coefficient were calculated. For an overview of these features and techniques, see [Bassett and Bullmore 2017](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5603984/),
and for an example of the techniques applied, see [Churchill et al 2021](https://www.nature.com/articles/s41598-021-85811-4). This is
convenient for us to do when given a pre-extracted ICA signal, like the [UkBioBank does](https://biobank.ctsu.ox.ac.uk/crystal/crystal/docs/brain_mri.pdf)
The second idea is to project an atlas, in our case [the Brainnetome atlas](https://atlas.brainnetome.org/), and also extract time series and graph network
features from the MRI projected regions. In addition to that we can look at relative probabilistic size of each region, signal variance from each region, 
and those regions will have direct labels to brain structures, unlike the ICA regions. 

This package has command line tools for the following
1. Batch feature extraction. Outputs will be json files read like python dictionaries for each individual brain
   >batch_feature_extraction.py
2. Graph network feature extraction for a UKBB ICA file
   >extract_ICA_features.py
3. The same graph feature extraction that would apply to a UKBB ICA file, except working with CSV format (UKBB uses double space delimited which is a bit odd)
   >extract_graph_features_from_time_series.py
4. Brainnetome feature extraction
   >extract_volume_features.py


# Running BIDS feature extraction
### OPTIONAL Clean Installation
      Likely Only Necessary if One Had Package Version Problems- 
1. First navigate to the directory you imported code into. Create a new Anaconda environment with python 3.9 to house the project with the right versions of software.
   > conda create --name extract --file requirements.txt

2. Run `export PYTHONPATH=$PYTHONPATH:.`

To extract features from the UkBioBank data folders, one must 

3. fill in the config file with their desired output destination and other variables. Explanations of each variable are included in the config file.
4. run batch_feature_extraction.py with nohup, which allows the user's code to continue running even after they have logged out of the cluster.
   >nohup python feature_extraction/batch_feature_extraction.py 
   
Note: One can let most features be default and only specify their output folder and number of mris with the command line. For example:
   >python feature_extraction/batch_feature_extraction.py --n_mris 10 --output_directory my/output/directory

### Command Line Options

One should be able to configure all of their settings except for mandatory inputs simply by altering the config.py file. However in some cases it is helpful in scripting
to have command line options, so the following options were added for ease of use. Below are a description and example for each option.
1. Batch feature extraction: n-mris (number of mris) and output_directory
   >batch_feature_extraction.py --n_mris 10 output_directory my/directory/
2. ICA feature extraction: ica_file (input file), output_file, and get_correlations (Boolean whether to add region vs region correlations into the feature dictionary)
   >extract_ICA_features.py --ica_file /utilities/example-ica-25.txt --output_file output.json --get_correlations True
3. Graph feature extraction: time_series_file (input file), output_file, and get_correlations (Boolean)
   >extract_graph_features_from_time_series.py --time_series_file my_input.csv --output_file output.json --get_correlations True
4. Brainnetome feature extraction: patient_MRI (input MRI file), output_file, brainnetome_in_patient_space (the Brainnetome 
atlas in utilities, after applying an inverse transform to put it into the shape of the patient's brain, in .nii.gz format), 
get_correlations and get_graph_features (Booleans)
   >extract_volume_features.py --patient_MRI my_brain.nii.gz --output_file output.json --brainnetome_in_patient_space inverse_brainnetome.nii.gz --get_correlations False --get_graph_features True


# Package file structure/organization

This repository is divided into three folders with their contents listed below:
1. the config folder
   1. config.py: needed for setting parameters and input/output locations
2. the feature extraction package
   1. The extraction_utils.py file which has the function definitions for getting features. 
   2. the scripts for calling python from the command line (batch_feature_extraction.py, etc)
   3. init.py
3. Utilities folder
   1. BNA-prob-2mm.nii.gz is a probabalistic atlas from Brainnetome, with 2mm size voxels.
   2. BNA_subregions.csv is a file with the regions and corresponding subregions of the Brainnetome atlas listed out
   3. brainnetome_gyri_vol.csv contains the probabilistic volume of the Brainnetome atlas for each gyrus, for the purposes of comparing patients brains
   4. brainnetome_lobes_vol.csv contains the same thing, except at a higher organizational level
   5. example-ica-25.csv is a (with noise added for anonymity) example of the typical input for extract_ICA_features, since UKBB formatted it uniquely

# Full list of extracted variables:
### Graph features
1. Isolated Nodes
2. Isolated Pairs (Two nodes connected by an edge but not connected to anywhere else)
3. Isolated Trios 
4. Count of Non-Isolated Nodes
5. Global Efficiency
6. Local Efficiency
7. Small-World Coefficient I (omega)
8. Small-World Coefficient II (sigma)
9. Average Shortest Path Length
10. Average Node Connectivity
11. Graph Density
12. Clustering Coefficient
13. Transitivity
14. Number of Subgraphs
### Correlation features
15. Between-region signal correlation
### Brainnetome features
16. Probabilistic volume of entire brain
17. Probabilistic volume of regions on lobe organizational level
18. Probabilistic volume of regions on gyrus organizational level
19. Probabilistic volume of all regions calculated as a proportion to the atlas
20. Signal variance of regions on both lobe and organizational level
-- Features #1-15 repeated on the graph generated with lobe/gyri region signals
### ICA features
-- Features #1-15 repeated on the graph generated with ICA signals

# Methods Appendix
### On Inverse Transforms
Inverse transforms weren't included as individual functions in this package even though they are used in batch_feature_extraction, because in our case the 
commands are given through FSL. The Brainnetome is in MNI space, and we already have the patient->MNI warp field, so in our cases we only needed to inverse that warp field 
and apply it to the Brainnetome atlas. The order of commands we use are:
   >fsl5.0-invwarp --ref=example_brain.nii.gz --warp=patient_to_MNI_warpfield.nii.gz --out=inverse_warpfield.nii.gz
   >fsl5.0-applywarp --ref=example_brain.nii.gz --in=utilities/BNA-prob-2mm.nii.gz --out=inverse_brainnetome.nii.gz  --warp=inverse_warpfield.nii.gz

If the user don't have a patient->MNI warp field precomputed, they will want to calculate that with [FNIRT](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FNIRT/UserGuide)

### On Graph Splitting
Many graph statistics do not function when a graph is not fully connected. Depending on graph connection thresholds chosen by the user as well, it is likely some graphs will 
have isolated single nodes or splits of regions with different sizes. In the situation where a graph of 25 nodes has a 5 node subgraph and 20 node subgraph that
are disconnected from each-other, the code is set up to split those subgraphs off and perform graph analysis on them individually. Then the final statistics are calculated with each 
subgraph being weighted by their size (80% and 20% respectively, in this example)

