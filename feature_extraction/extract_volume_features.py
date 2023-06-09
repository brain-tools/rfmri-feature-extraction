import numpy as np
from config.config import *
import argparse
from nilearn import image
from nilearn.maskers import NiftiMapsMasker

from feature_extraction.extraction_utils import region_feature_extraction, atlas_time_series_feature_extraction

CLI = argparse.ArgumentParser()
CLI.add_argument(
    "--patient_MRI",
    nargs="*",
    type=str,
    default='',
)
CLI.add_argument(
    "--output_file",
    nargs="*",
    type=str,
    default=data_directory,
)
CLI.add_argument(
    "--get_correlations",
    nargs="*",
    type=bool,
    default=return_correlations,
)
CLI.add_argument(
    "--get_graph_features",
    nargs="*",
    type=bool,
    default=return_correlations,
)
CLI.add_argument(
    "--brainnetome_in_patient_space",
    nargs="*",
    type=bool,
    default="",
)
args = CLI.parse_args()
base_mri = args.patient_MRI[0]
features_file = args.output_file[0]
get_correlations = args.get_correlations[0]
get_graph_features = args.get_graph_features[0]
brain = image.load_img(base_mri)
inverse_brainnetome = args.brainnetome_in_patient_space[0]
inverse_brainnetome_sitk = sitk.GetArrayFromImage(sitk.ReadImage(inverse_brainnetome))
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
                                                                     get_graph_features, get_correlations)
    lobe_time_series_features = atlas_time_series_feature_extraction(lobe_time_series, THRESHOLDS, \
                                                                     get_graph_features, get_correlations)
    gyri_volume_features = region_feature_extraction(gyri_vol, brainnetome_gyri_vol)
    lobe_volume_features = region_feature_extraction(lobe_vol, brainnetome_lobe_vol)
    for sub_features in [gyri_time_series_features, lobe_time_series_features, gyri_volume_features, \
                         lobe_volume_features]:
        features.update(sub_features)
    ## Write features
    with open(features_file, 'w') as data:
        data.write(str(features))

except:
    print("extraction failed, try repeating with graph feature extraction turned off if it is on")
