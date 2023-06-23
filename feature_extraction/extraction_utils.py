import pandas as pd
import networkx as nx
import numpy as np


def graph_from_corr_matrix(corr_matrix, threshold, valid_regions):
    """
    function to get a graph from a correlation matrix - taking edges where correlations above threshold
    :param corr_matrix: numpy matrix with correlation data
    :param threshold: threshold used to calculate graph connections
    :param valid_regions: a list of valid regions, pertinent to ICA where some ICA regions are unhelpful
    :return: networkx graph "g"
    """
    corr = pd.DataFrame(corr_matrix)
    # Transform it in a links data frame (3 columns only):
    links = corr.stack().reset_index()
    links.columns = ['var1', 'var2', 'value']

    # Keep only correlation over a threshold and remove self correlation (cor(A,A)=1)
    links_filtered = links.loc[(np.abs(links['value']) > threshold) & (links['var1'] != links['var2'])]

    # Build the graph
    g = nx.from_pandas_edgelist(links_filtered, 'var1', 'var2')
    g.add_nodes_from(range(0, len(corr)))
    g = remove_unwanted_ica_regions(valid_regions, g)
    return (g)


def remove_unwanted_ica_regions(ica_valid_regions, graph):
    """
    ica from UK biobank stipulates that some ica regions are invalid, so this function makes it possible to remove them
    :param ica_valid_regions: List of int
    :param graph: networkx graph
    :return: networkx graph
    """
    if len(ica_valid_regions)>0:
        for node in list(graph.nodes):
            if node not in ica_valid_regions:
                graph.remove_node(node)
    return (graph)


def instantiate_graph_features():
    '''
    because we iterate over subgraphs and get features individually, it helps to have a dictionary to sum up
    graph features throughout the process - instantiating beforehand to set most features to zero for summing
    :return: a dictionary of features
    '''
    features = {}
    GRAPH_FEATURES = ['Isolated Nodes', 'Isolated Pairs', 'Isolated Trios', 'Global Efficiency', \
                      'Local Efficiency', 'Omega Zero Denominator', 'Omega', 'Sigma Zero Denominator', 'Sigma', 'Average Shortest Path Length', 'Average Node Connectivity', \
                      'Density', 'Average Clustering', 'Transitivity']
    for feature in GRAPH_FEATURES:
        features[feature] = 0
    features['Subgraphs'] = 1
    return (features)


def get_subgraphs(graph):
    """
    split a graph into a list of subgraphs - only to be called when the graph is incomplete
    :param graph: networkx graph
    :return: list of networkx graphs
    """
    subgraphs = []
    sub_graph_iterator = nx.connected_components(graph)
    for s_g_i in sub_graph_iterator:
        subgraph = graph.subgraph(list(s_g_i))
        subgraphs.append(subgraph)
    return (subgraphs)


# get density of a graph (ratio of edges divided by number of possible edges)
def get_density(graph):
    n_nodes = len(graph.nodes)
    return 2 * len(graph.edges) / (n_nodes * (n_nodes - 1))


def get_small_world_features(graph, features, normalization_term=1):
    """
    add all graph statistics to the features dictionary, mostly using the networkx package to calculate staistics
    :param graph: networkx graph
    :param features: dictionary of features
    :param normalization_term: a float or int used to weight how much a subraph contributes to the feature score
    :return: features dictionary
    """
    # For sigma and omega, networkx generates random equivalent graphs that can have zero-denominator statistics
    try:
        sigma = nx.sigma(graph)
        if not isinstance(sigma, (int, float)):
            features['Sigma'] += sigma * normalization_term
        else:
            features['Sigma Zero Denominator'] += normalization_term
    except:
        features['Sigma Zero Denominator'] += normalization_term
    try:
        omega = nx.omega(graph)
        if not isinstance(omega, (int, float)):
            features['Omega'] += omega * normalization_term
        else:
            features['Omega Zero Denominator'] += normalization_term
    except:
        features['Omega Zero Denominator'] += normalization_term
    features['Local Efficiency'] += nx.local_efficiency(graph) * normalization_term
    features['Global Efficiency'] += nx.global_efficiency(graph) * normalization_term
    features['Average Shortest Path Length'] += nx.average_shortest_path_length(graph) * normalization_term
    features['Average Node Connectivity'] += nx.average_node_connectivity(graph) * normalization_term
    features['Density'] += get_density(graph) * normalization_term
    features['Average Clustering'] += nx.average_clustering(graph) * normalization_term
    features['Transitivity'] += nx.transitivity(graph) * normalization_term
    return (features)


# for a subgraph too small to generate graph statistics, tally how many of them were in the graph
def tally_graph_fragment(subgraph, features):
    if len(subgraph.nodes) == 1:
        features['Isolated Nodes'] += 1
    elif len(subgraph.nodes) == 2:
        features['Isolated Pairs'] += 1
    elif len(subgraph.nodes) == 2:
        features['Isolated Trios'] += 1
    return (features)


def get_graph_statistics(graph):
    """
    Calculate features from a graph
    :param graph: networkx graph
    :return: dictionary of features
    """
    features = instantiate_graph_features()
    if nx.is_connected(graph):
        features['Non-isolated Nodes'] = len(graph.nodes)
        return (get_small_world_features(graph, features))
    else:
        subgraphs = get_subgraphs(graph)
        features['Subgraphs'] = len(subgraphs)
        features['Non-isolated Nodes'] = sum(len(subgraph.nodes) for subgraph in subgraphs \
                                             if len(subgraph.nodes) > 3)
        return (get_statistics_from_subgraph_set(subgraphs, features))


def get_statistics_from_subgraph_set(subgraphs, features):
    """
    Because many graphs have discontinuities, they need to be broken apart and statistics are summed up from each subgraph
    :param subgraphs: List of networkx graphs
    :param features: feature dictionary
    :return: feature dictionary
    """
    for i, subgraph in enumerate(subgraphs):
        if len(subgraph.nodes) < 4:
            features = tally_graph_fragment(subgraph, features)
        else:
            # smaller subgraphs get weighted less for the overall statistic, so we need a weighting term
            subgraph_normalization_term = len(subgraph.nodes) / features['Non-isolated Nodes']
            get_small_world_features(subgraph, features, subgraph_normalization_term)
    return (features)


def ICA_graph_feature_extraction(ica_file, thresholds, valid_regions, add_correlation_features=False):
    """
    take an ICA file from UKBiobank and return a dictionary of features from this file
    :param ica_file: a space delimited file of signals from each ICA region, an example is provided in utilities
    :param thresholds: list of float, necessarily between 0 and 1
    :param valid_regions: list of int
    :param add_correlation_features: Boolean - since correlations are already calculated one can add correlations between regions as a feature
    :return: dictionary of features
    """
    features = {}
    df = pd.read_csv(ica_file, sep="  ", header=None, engine='python')
    #Add signal variances as features as well
    ts_df = df.T
    for index, row in ts_df.iterrows():
        var_str = str('ICA region ' + str(index) + ' Signal Variance')
        features[var_str] = np.var(row)
    # Now calculate correlations to generate a graph with
    corr = df.corr()
    if add_correlation_features:
        features = get_correlation_features(corr, features, "ICA Regions: ")
    corr = corr.to_numpy()
    for threshold in thresholds:
        graph = graph_from_corr_matrix(corr, threshold, valid_regions)
        statistics = get_graph_statistics(graph)
        for k, v in statistics.items():
            new_key = 'ICA ' + k + ' at Threshold ' + str(threshold)
            features[new_key] = v
    return (features)


def atlas_time_series_feature_extraction(time_series_df, thresholds=[], add_network_features=False,
                                         add_correlation_features=False):
    """
    Function that calculates signal variance of regions of the brain as extracted from brainnetome labeled areas
    :param time_series_df: pandas dataframe with indices as brain region labels and columns that make a signal
    :param thresholds: thresholds with which to make a graph from correlation matrix
    :param add_network_features: Bool: if True, will calculate network features from the graph made by the correlation matrix and given thresholds
    :param add_correlation_features: Bool
    :return: a dictionary of features
    """
    features = {}
    for index, row in time_series_df.iterrows():
        var_str = str(index.strip() + ' Signal Variance')
        features[var_str] = np.var(row)
    if add_network_features or add_correlation_features:
        corr = time_series_df.transpose().corr()
    if add_correlation_features:
        features = get_correlation_features(corr, features)
    if add_network_features:
        corr = corr.to_numpy()
        # all regions are valid for this
        valid_regions = list(np.arange(len(corr)))
        for threshold in thresholds:
            graph = graph_from_corr_matrix(corr, threshold, valid_regions)
            statistics = get_graph_statistics(graph)
            for k, v in statistics.items():
                new_key = 'Brainnetome Gyri ' + k + ' at Threshold ' + str(threshold)
                features[new_key] = v
    return (features)


# define a method for region volume feature extraction
def region_feature_extraction(inv_vol, brainnetome_vol):
    """

    :param inv_vol: pandas dataframe representing volume (as in the 3-d measurement) of brain regions from a patient's brain
    inverse transformed
    :param brainnetome_vol: the brainnetome atlas.
    :return: a feature dictionary containing the percent of the volume each region takes up, plus that volume's relative size compared
    to the brainnetome atlas
    """
    features = {}
    for index, row in inv_vol.iterrows():
        feature_str = str(index.strip() + ' Percent of Total Volume')
        relative_str = str(index.strip() + ' Percent of Total Volume Relative To Atlas')
        features[feature_str] = inv_vol.loc[index]['percent_vol']
        features[relative_str] = inv_vol.loc[index]['percent_vol'] / brainnetome_vol.loc[index]['percent_vol']
    return (features)

def get_correlation_features(corr_df, feature_dict, prefix=''):
    """
    Function to put correlations (already computed) into the feature return.
    in this function instead of a correlation numpy array , we have to pass a correlation pandas dataframe to preserve the names of the rows
    :param corr_df: pandas dataframe
    :param feature_dict: existing dictionary of features for an MRI, the correlations are loaded into this
    :param prefix: this string is optional,
    :return: return the expanded feature dictionary.
    """
    # remove redundant and diagonal entries from the correlation
    corr = corr_df.where(np.invert(np.triu(np.ones(corr_df.shape)).astype(np.bool)))
    # stack dataframe into one pandas.Series for easier iterations
    corr = corr.stack()
    # add each correlation into the dictionary of features
    for index, value in corr.items():
      key = "Correlation " + prefix + str(index[0]) + " vs " + str(index[1])
      key = key.strip()
      feature_dict[key] = value
    return (feature_dict)
