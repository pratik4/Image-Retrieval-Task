import json
from os.path import basename, join, isfile
from functools import lru_cache

import numpy as np
from sklearn.externals import joblib

from src.model import loadModel
from src.features import representation_size

class SearchModel:


    def __init__(self, features_path, ):
        # Load the extraction model
        self.model = loadModel()

        # Load the feature metadata
        features_basename = basename(features_path)
        meta_file_path = join(features_path,
                              '{}.meta'.format(features_basename))
        with open(meta_file_path, 'r') as f:
            self.feature_metadata = json.load(f)

        # Load image representations
        repr_file_path = join(features_path,
                              '{}.repr.npy'.format(features_basename))
        self.feature_store = np.load(repr_file_path)

        if representation_size(self.model) != self.feature_store.shape[-1]:
            raise ValueError('Model {} and feature store {} have nonmatching '
                             'representation sizes: {} vs {}'.format(
                                model, features_path,
                                representation_size(self.model),
                                self.feature_store.shape[-1]))

        # Construct paths to feature files
        self.feature_file_paths = {}
        features_sub_folder = join(features_path, 'features/')
        for idx, metadata in self.feature_metadata.items():
            if not idx.isdigit():
                continue
            image_name = basename(self.feature_metadata[str(idx)]['image'])
            path = join(features_sub_folder, '{}.npy'.format(image_name))
            if isfile(path):
                self.feature_file_paths[str(idx)] = path
            else:
                print('Missing feature file for image {}'.format(image_name))

        # Load PCA
        pca_file_path = join(features_path, '{}.pca'.format(features_basename))
        if isfile(pca_file_path):
            self.pca = joblib.load(pca_file_path)
        else:
            self.pca = None


    def get_metadata(self, feature_idx):
        return self.feature_metadata[str(feature_idx)]

    @lru_cache(maxsize=128)
    def get_features(self, feature_idx):
        feature_idx = str(feature_idx)
        feature_file_path = self.feature_file_paths[feature_idx]
        features = np.load(feature_file_path)
        self.feature_metadata[feature_idx]['feature_height'] = features.shape[0]
        self.feature_metadata[feature_idx]['feature_width'] = features.shape[1]
        return features
