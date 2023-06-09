import errno
from os.path import exists
from config.config import *
import argparse
from feature_extraction.extraction_utils import ICA_graph_feature_extraction, get_correlation_features, \
    graph_from_corr_matrix, get_graph_statistics


def graph_feature_extraction(ica_file, thresholds, valid_regions, add_correlation_features=False):
    """
    take a CSV delimited time series and extract graph features
    :param ica_file: a space delimited file of signals from each ICA region, an example is provided in utilities
    :param thresholds: list of float, necessarily between 0 and 1
    :param valid_regions: list of int
    :param add_correlation_features: Boolean - since correlations are already calculated one can add correlations between regions as a feature
    :return: dictionary of features
    """
    features = {}
    df = pd.read_csv(ica_file, header=None, engine='python')
    corr = df.corr()
    if add_correlation_features:
        features = get_correlation_features(corr, features, "Regions: ")
    corr = corr.to_numpy()
    for threshold in thresholds:
        graph = graph_from_corr_matrix(corr, threshold, valid_regions)
        statistics = get_graph_statistics(graph)
        for k, v in statistics.items():
            new_key = k + 'at Threshold ' + str(threshold)
            features[new_key] = v
    return (features)

CLI = argparse.ArgumentParser()
CLI.add_argument(
    "--time_series_file",
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
time_series_file = args.time_series_file[0]
features_file = args.output_file[0]
get_correlations = args.get_correlations[0]


if not exists(time_series_file):
    raise FileNotFoundError(
        errno.ENOENT, os.strerror(errno.ENOENT), time_series_file)
features = {}
try:
    ica_features = graph_feature_extraction(time_series_file, THRESHOLDS, valid_ica_regions, get_correlations)
    with open(features_file, 'w') as data:
        data.write(str(ica_features))
except:
    print('extraction failed for ICA network analysis. Some likely causes of this are 1) thresholds are too high, creating a\
    very fragmented graph. Suggestion for debugging is to see the size of subgraphs where the error is thrown.')

