from config.config import *
from extraction_utils import *
import argparse
from datetime import datetime
from os.path import exists
from nilearn import image
from nilearn.maskers import NiftiMapsMasker
from matplotlib import pyplot as plt
import SimpleITK as sitk

## Read in user commands
CLI = argparse.ArgumentParser()
CLI.add_argument(
    "--n_mris",
    nargs="*",
    type=int,
    default=n_mris,
)
CLI.add_argument(
    "--output_directory",
    nargs="*",
    type=str,
    default=data_directory,
)
args = CLI.parse_args()
n_mris = args.n_mris[0]
data_directory = args.output_directory[0]

folders = [os.path.join(bids, folder) for folder in os.listdir(bids) if os.path.isdir(os.path.join(bids, folder))]
files_visited = 0
folders_without_necessary_files = 0
feature_extraction_failures = 0
failed_extraction_ids = []
for folder in folders:
    # try to enter folder and load data - skip folders with no data or unloadable data
    try:
        os.chdir(str(folder + '/ses-2/func'))
        cwd = os.getcwd()
        new_cwd = True
        files = [f for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
        patient = cwd.split('/')[-3]
        # make sure we have needed files, try loading our MRI
        ica_time_series_file = patient + '_ses-2_task-rest_ts-ica-25.txt'
        base_mri = patient + '_ses-2_task-rest_filtered-clean.nii.gz'
        features_file = data_directory + 'feature_dicts/' + patient + '_ses-2_task-rest_network_features.json'
        if not exists(features_file):
            brain = image.load_img(base_mri)
    except:
        folders_without_necessary_files += 1
        new_cwd = False
    if new_cwd and exists(ica_time_series_file) and not exists(features_file):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        if verbose == True:
            print('on mri # ' + str(files_visited) + ' patient ' + str(patient))
            print("Current Time =", current_time)

        ## Then we name the files we will create with FSL
        patient_inverse_warp_field = data_directory + patient + '_ses-2_task-rest_mni2func-warp.nii.gz'
        inverse_brainnetome = data_directory + patient + '_ses-2_task-rest_inverse_brainnetome.nii.gz'

        ##using FSL command line, inverse a warp and apply it to the brainnetome atlas, only when this file doesn't already exist
        if not exists(inverse_brainnetome):
            inv_warp_command = 'fsl5.0-invwarp --ref=' + patient + '_ses-2_task-rest_filtered-clean.nii.gz --warp=' + \
                               patient + '_ses-2_task-rest_func2mni-warp.nii.gz --out=' + patient_inverse_warp_field
            os.system(inv_warp_command)
            apply_inv_command = 'fsl5.0-applywarp --ref=' + base_mri + ' --in=' + brainnetome_file + \
                                ' --out=' + inverse_brainnetome + '  --warp=' + patient_inverse_warp_field
            os.system(apply_inv_command)

        ##Now we load the inverse we just made with SITK so we can manipulate a numpy array from it
        inverse_brainnetome_sitk = sitk.GetArrayFromImage(sitk.ReadImage(inverse_brainnetome))

        ##Extract a time series from the loaded brain based on the inverse brainnetome atlas
        masker = NiftiMapsMasker(maps_img=inverse_brainnetome, standardize=True)
        time_series = masker.fit_transform(brain)

        ## Add the probabilistic volume of each region, calculate the size of gyri and lobes
        regions['vol'] = np.sum(inverse_brainnetome_sitk, axis=(1, 2, 3))
        gyri_vol = regions[['Gyrus', 'vol']].groupby('Gyrus').sum()
        gyri_vol['percent_vol'] = (gyri_vol['vol'] / gyri_vol['vol'].sum()) * 100
        lobe_vol = regions[['Lobe', 'vol']].groupby('Lobe').sum()
        lobe_vol['percent_vol'] = (lobe_vol['vol'] / lobe_vol['vol'].sum()) * 100

        ## Put the time series together with the region+subregion groupings and aggregate
        labeled_time_series = pd.concat([regions, pd.DataFrame(time_series.T)], axis=1)
        gyri_time_series = labeled_time_series.drop(columns=['Lobe', 'Number', 'vol'])
        gyri_time_series = gyri_time_series.groupby(['Gyrus']).mean()
        lobe_time_series = labeled_time_series.drop(columns=['Gyrus', 'Number', 'vol'])
        lobe_time_series = lobe_time_series.groupby(['Lobe']).mean()

        ## Collect features
        features = {}
        try:
            features['Total Probabilistic Voxel Volume In Target Regions'] = np.sum(regions['vol'])
            features['Total Probabalistic Voxel Volume Proportional To Atlas Volume'] = \
                np.sum(regions['vol']) / np.sum(brainnetome_lobe_vol['vol'])
            gyri_time_series_features = atlas_time_series_feature_extraction(gyri_time_series, THRESHOLDS, \
                                                                             return_graph_features, return_correlations)
            lobe_time_series_features = atlas_time_series_feature_extraction(lobe_time_series, THRESHOLDS, \
                                                                             return_graph_features, return_correlations)
            gyri_volume_features = region_feature_extraction(gyri_vol, brainnetome_gyri_vol)
            lobe_volume_features = region_feature_extraction(lobe_vol, brainnetome_lobe_vol)
            ica_features = ICA_graph_feature_extraction(ica_time_series_file, THRESHOLDS, valid_ica_regions, return_correlations)
            for sub_features in [gyri_time_series_features, lobe_time_series_features, gyri_volume_features, \
                                 lobe_volume_features, ica_features]:
                features.update(sub_features)
            ## Write features to output
            with open(features_file, 'w') as data:
                data.write(str(features))
            files_visited += 1
        except:
            feature_extraction_failures += 1
            failed_extraction_ids.append(patient)
            print('extraction failed for ' + str(patient))

    if files_visited >= n_mris:
        break
    if folders_without_necessary_files == max_files:
        break
if verbose:
    print(str(files_visited) + ' MRIs were processed for feature extraction')
    print(str(folders_without_necessary_files) + " MRI folders were visited but they lacked necessary files for extraction")
    print(str(feature_extraction_failures) + 'MRIs had an error in feature extraction, their IDs were:')
    print(failed_extraction_ids)
