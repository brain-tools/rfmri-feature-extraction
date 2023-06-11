import pandas as pd
import os

path = os.getcwd()

# Set directory you would like to store data in
data_directory = 'USER_FILL'

# Set the location of the Brainnetome Atlas and read CSV files with preprocessed data extracted from the atlas
brainnetome_file = '/utilities/BNA-prob-2mm.nii.gz'
regions = pd.read_csv('utilities/BNA_subregions.csv')
brainnetome_lobe_vol = pd.read_csv('utilities/brainnetome_lobes_vol.csv', index_col=0)
brainnetome_gyri_vol = pd.read_csv('utilities/brainnetome_gyri_vol.csv', index_col=0)

# Folder directory that holds MRI data
bids = '/ritter/share/data/UKBB/ukb_data/bids'

# Valid ICA regions for UK Biobank https://biobank.ctsu.ox.ac.uk/crystal/crystal/docs/brain_mri.pdf
valid_ica_regions = '1  2  3  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22'
valid_ica_regions = [int(x) - 1 for x in valid_ica_regions.split()]

# Minimum Correlation thresholds you choose for the creation of graph edges.
THRESHOLDS = [.25, .35]

# Number of MRIs you would like to collect data from
n_mris = 50

# Maximum number of folder directories you would like to traverse before quitting the program (stop infinite runs)
max_files = 25000

# Choose to print updates on patient IDs so the user knows how far it has run
verbose = True

# Return correlations as a feature
return_correlations = False

# Return graph features for volume extraction
return_graph_features = True

