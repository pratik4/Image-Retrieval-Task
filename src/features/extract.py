from math import floor

import numpy as np

from src.util import normalize

def _region_generator(array, size, overlap, verbose=False):
    """A generator which returns square overlapping regions"""
    height, width = array.shape[0], array.shape[1]
    row = 0
    while row < height:
        row_end = min(row + size, height)

        col = 0
        while col < width:
            col_end = min(col + size, width)
            if verbose:
                print('Current region: row {}:{}, col {}:{}'.format(
                    row, row_end, col, col_end))

            yield array[row:row_end, col:col_end]

            if col + size == width:
                break
            col = round(col + (1 - overlap) * (col + size))

        if row + size == height:
            break
        row = round(row + (1 - overlap) * (row + size))


def _compute_mac(features):
    """
    Computes maximum activations of convolutions, which is the
    maximum across the spatial dimensions of the features.
    """
    return np.amax(features, axis=(0,1))


def compute_r_macs(features, scales=(1, 4), verbose=False):
    """
    Computes regional maximum activations of convolutions
    (see arXiv:1511.05879v2)

    Args:
    scales: inclusive interval from which the scale parameter l is chosen
        from, where l=1 is a square region filling the whole image.
        Higher scales result in smaller regions following the formula
        given in the paper on p.4

    Returns: list of r_mac vectors of shape (1, N), where N is the
    depth of the convolutional feature maps
    """
    assert len(features.shape) == 3
    height, width = features.shape[0], features.shape[1]

    r_macs = []
    for scale in range(scales[0], scales[1]+1):
        r_size = max(floor(2 * min(height, width) / (scale + 1)), 1)
        if verbose:
            print('Region width at scale {}: {}'.format(scale, r_size))

        # Uniform sampling of square regions with 40% overlap
        for region in _region_generator(features, r_size, 0.4):
            r_mac = _compute_mac(region)
            r_mac = normalize(np.expand_dims(r_mac, axis=0))
            r_macs.append(r_mac)

        if r_size == 1:
            break
    return r_macs


def _compute_global_r_mac(features, pca=None):

    assert len(features.shape) == 3

    global_r_mac = np.zeros((1, features.shape[2]))  # Sum of all regional features
    macs = compute_r_macs(features)

    for mac in macs:
        if pca:
            mac = pca.transform(mac)
            mac = normalize(mac)
        global_r_mac += mac

    return normalize(global_r_mac)


def compute_features(model, image):

    features = model.predict(image)
    features = np.squeeze(features, axis=0)
    return features


def compute_representation(features, pca=None):

    global_r_mac = _compute_global_r_mac(features, pca)
    return global_r_mac


def compute_localization_representation(features):

    mac = _compute_mac(features)
    return normalize(mac)


def representation_size(model):
    return model.output_shape[3]
