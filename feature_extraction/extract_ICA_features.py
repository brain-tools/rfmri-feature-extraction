import errno
from os.path import exists
from config.config import *
import argparse
from feature_extraction.extraction_utils import ICA_graph_feature_extraction


CLI = argparse.ArgumentParser()
CLI.add_argument(
    "--ica_file",
    nargs="*",
    type=int,
    default=n_mris,
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
args = CLI.parse_args()
ica_time_series_file = args.ica_file[0]
features_file = args.output_file[0]
get_correlations = args.get_correlations[0]


if not exists(ica_time_series_file):
    raise FileNotFoundError(
        errno.ENOENT, os.strerror(errno.ENOENT), ica_time_series_file)
features = {}
try:
    ica_features = ICA_graph_feature_extraction(ica_time_series_file, THRESHOLDS, valid_ica_regions, get_correlations)
    with open(features_file, 'w') as data:
        data.write(str(ica_features))
except:
    print('extraction failed for ICA network analysis. Some likely causes of this are 1) thresholds are too high, creating a\
    very fragmented graph. Suggestion for debugging is to see the size of subgraphs where the error is thrown.')

