"""
Algorithms for computing the skeleton of a binary image
"""

import numpy as np
from scipy import ndimage as ndi

from ._skeletonize_cy import _fast_skeletonize, _skeletonize_loop, _table_lookup_index

# --------- Skeletonization by morphological thinning ---------

def skeletonize(image):
    """Return the skeleton of a binary image.

    Thinning is used to reduce each connected component in a binary image
    to a single-pixel wide skeleton.

    Parameters
    ----------
    image : numpy.ndarray
        A binary image containing the objects to be skeletonized. '1'
        represents foreground, and '0' represents background. It
        also accepts arrays of boolean values where True is foreground.

    Returns
    -------
    skeleton : ndarray
        A matrix containing the thinned image.

    See also
    --------
    medial_axis

    Notes
    -----
    The algorithm [Zha84]_ works by making successive passes of the image,
    removing pixels on object borders. This continues until no
    more pixels can be removed.  The image is correlated with a
    mask that assigns each pixel a number in the range [0...255]
    corresponding to each possible pattern of its 8 neighbouring
    pixels. A look up table is then used to assign the pixels a
    value of 0, 1, 2 or 3, which are selectively removed during
    the iterations.

    Note that this algorithm will give different results than a
    medial axis transform, which is also often referred to as
    "skeletonization".

    References
    ----------
    .. [Zha84] A fast parallel algorithm for thinning digital patterns,
           T. Y. Zhang and C. Y. Suen, Communications of the ACM,
           March 1984, Volume 27, Number 3.


    Examples
    --------
    >>> X, Y = np.ogrid[0:9, 0:9]
    >>> ellipse = (1./3 * (X - 4)**2 + (Y - 4)**2 < 3**2).astype(np.uint8)
    >>> ellipse
    array([[0, 0, 0, 1, 1, 1, 0, 0, 0],
           [0, 0, 1, 1, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 1, 1, 0, 0],
           [0, 0, 0, 1, 1, 1, 0, 0, 0]], dtype=uint8)
    >>> skel = skeletonize(ellipse)
    >>> skel.astype(np.uint8)
    array([[0, 0, 0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 1, 0, 0, 0, 0],
           [0, 0, 0, 0, 1, 0, 0, 0, 0],
           [0, 0, 0, 0, 1, 0, 0, 0, 0],
           [0, 0, 0, 0, 1, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0, 0, 0]], dtype=uint8)

    """

    # convert to unsigned int (this should work for boolean values)
    image = image.astype(np.uint8)

    # check some properties of the input image:
    #  - 2D
    #  - binary image with only 0's and 1's
    if image.ndim != 2:
        raise ValueError('Skeletonize requires a 2D array')
    if not np.all(np.in1d(image.flat, (0, 1))):
        raise ValueError('Image contains values other than 0 and 1')

    return _fast_skeletonize(image)

# Alternate skeletonization by thinning algorithm

G123_LUT = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1,
       0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0,
       1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
       0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1,
       0, 0, 0], dtype=np.bool)

G123P_LUT = np.array([0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0,
       1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0,
       0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0,
       1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1,
       0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0], dtype=np.bool)

def thin(image, max_iter=None):
    """
    Perform morphological thinning of a binary image.
    
    Parameters
    ----------
    image : binary (M, N) ndarray
        The image to be thinned.
    
    max_iter : int, number of iterations, optional
        Regardless of the value of this parameter, the thinned image
        is returned immediately if an iteration produces no change.
        If this parameter is specified it thus sets an upper bound on
        the number of iterations performed.
    
    Returns
    -------
    out : ndarray of bools
        Thinned image.
    
    See also
    --------
    skeletonize, skeletonize_3d, medial_axis
    
    Notes
    -----
    This algorithm [1]_ works by making multiple passes over the image,
    removing pixels matching a set of criteria designed to thin
    connected regions while preserving eight-connected components and
    2 x 2 squares [2]_. In each of the two sub-iterations the algorithm
    correlates the intermediate skeleton image with a neighborhood mask,
    then looks up each neighborhood in a lookup table indicating whether
    the central pixel should be deleted in that sub-iteration.
    
    References
    ----------
    .. [1] Z. Guo and R. W. Hall, "Parallel thinning with
           two-subiteration algorithms," Comm. ACM, vol. 32, no. 3,
           pp. 359-373, 1989.
    .. [2] Lam, L., Seong-Whan Lee, and Ching Y. Suen, "Thinning
           Methodologies-A Comprehensive Survey," IEEE Transactions on
           Pattern Analysis and Machine Intelligence, Vol 14, No. 9,
           September 1992, p. 879
    
    Examples
    --------
    >>> square = np.zeros((7, 7), dtype=np.uint8)
    >>> square[1:-1, 2:-2] = 1
    >>> square[0, 1] =  1
    >>> square
    array([[0, 1, 0, 0, 0, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 0, 0, 0, 0, 0]], dtype=uint8)
    >>> skel = thin(square)
    >>> skel.astype(np.uint8)
    array([[0, 1, 0, 0, 0, 0, 0],
           [0, 0, 1, 0, 0, 0, 0],
           [0, 0, 0, 1, 0, 0, 0],
           [0, 0, 0, 1, 0, 0, 0],
           [0, 0, 0, 1, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0]], dtype=uint8)
    """
    # check parameters
    if max_iter is None:
        n = -1
    elif max_iter <= 0:
        raise ValueError('max_iter must be > 0')
    else:
        n = max_iter
    
    # check that we have a 2d binary image, and convert it
    # to uint8
    skel = np.array(image).astype(np.uint8)
    
    if skel.ndim != 2:
        raise ValueError('2D array required')
    if not np.all(np.in1d(image.flat,(0,1))):
        raise ValueError('Image contains values other than 0 and 1')

    # neighborhood mask
    mask = np.array([[ 8,  4,  2],
                     [16,  0,  1],
                     [32, 64,128]], dtype=np.uint8)

    # iterate either 1) indefinitely or 2) up to iteration limit
    while n != 0:
        before = np.sum(skel) # count points before thinning
        
        # for each subiteration
        for lut in [G123_LUT, G123P_LUT]:
            # correlate image with neighborhood mask
            N = ndi.correlate(skel, mask, mode='constant')
            # take deletion decision from this subiteration's LUT
            D = np.take(lut, N)
            # perform deletion
            skel[D] = 0
            
        after = np.sum(skel) # coint points after thinning
        
        if before == after:
            # iteration had no effect: finish
            break
            
        # count down to iteration limit (or endlessly negative)
        n -= 1
    
    return skel.astype(np.bool)
    

# --------- Skeletonization by medial axis transform --------

_eight_connect = ndi.generate_binary_structure(2, 2)


def medial_axis(image, mask=None, return_distance=False):
    """
    Compute the medial axis transform of a binary image

    Parameters
    ----------
    image : binary ndarray, shape (M, N)
        The image of the shape to be skeletonized.
    mask : binary ndarray, shape (M, N), optional
        If a mask is given, only those elements in `image` with a true
        value in `mask` are used for computing the medial axis.
    return_distance : bool, optional
        If true, the distance transform is returned as well as the skeleton.

    Returns
    -------
    out : ndarray of bools
        Medial axis transform of the image
    dist : ndarray of ints, optional
        Distance transform of the image (only returned if `return_distance`
        is True)

    See also
    --------
    skeletonize

    Notes
    -----
    This algorithm computes the medial axis transform of an image
    as the ridges of its distance transform.

    The different steps of the algorithm are as follows
     * A lookup table is used, that assigns 0 or 1 to each configuration of
       the 3x3 binary square, whether the central pixel should be removed
       or kept. We want a point to be removed if it has more than one neighbor
       and if removing it does not change the number of connected components.

     * The distance transform to the background is computed, as well as
       the cornerness of the pixel.

     * The foreground (value of 1) points are ordered by
       the distance transform, then the cornerness.

     * A cython function is called to reduce the image to its skeleton. It
       processes pixels in the order determined at the previous step, and
       removes or maintains a pixel according to the lookup table. Because
       of the ordering, it is possible to process all pixels in only one
       pass.

    Examples
    --------
    >>> square = np.zeros((7, 7), dtype=np.uint8)
    >>> square[1:-1, 2:-2] = 1
    >>> square
    array([[0, 0, 0, 0, 0, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 1, 1, 1, 0, 0],
           [0, 0, 0, 0, 0, 0, 0]], dtype=uint8)
    >>> medial_axis(square).astype(np.uint8)
    array([[0, 0, 0, 0, 0, 0, 0],
           [0, 0, 1, 0, 1, 0, 0],
           [0, 0, 0, 1, 0, 0, 0],
           [0, 0, 0, 1, 0, 0, 0],
           [0, 0, 0, 1, 0, 0, 0],
           [0, 0, 1, 0, 1, 0, 0],
           [0, 0, 0, 0, 0, 0, 0]], dtype=uint8)

    """
    global _eight_connect
    if mask is None:
        masked_image = image.astype(np.bool)
    else:
        masked_image = image.astype(bool).copy()
        masked_image[~mask] = False
    #
    # Build lookup table - three conditions
    # 1. Keep only positive pixels (center_is_foreground array).
    # AND
    # 2. Keep if removing the pixel results in a different connectivity
    # (if the number of connected components is different with and
    # without the central pixel)
    # OR
    # 3. Keep if # pixels in neighbourhood is 2 or less
    # Note that table is independent of image
    center_is_foreground = (np.arange(512) & 2**4).astype(bool)
    table = (center_is_foreground  # condition 1.
                &
            (np.array([ndi.label(_pattern_of(index), _eight_connect)[1] !=
                       ndi.label(_pattern_of(index & ~ 2**4),
                                    _eight_connect)[1]
                       for index in range(512)])  # condition 2
                |
        np.array([np.sum(_pattern_of(index)) < 3 for index in range(512)]))
        # condition 3
            )

    # Build distance transform
    distance = ndi.distance_transform_edt(masked_image)
    if return_distance:
        store_distance = distance.copy()

    # Corners
    # The processing order along the edge is critical to the shape of the
    # resulting skeleton: if you process a corner first, that corner will
    # be eroded and the skeleton will miss the arm from that corner. Pixels
    # with fewer neighbors are more "cornery" and should be processed last.
    # We use a cornerness_table lookup table where the score of a
    # configuration is the number of background (0-value) pixels in the
    # 3x3 neighbourhood
    cornerness_table = np.array([9 - np.sum(_pattern_of(index))
                                 for index in range(512)])
    corner_score = _table_lookup(masked_image, cornerness_table)

    # Define arrays for inner loop
    i, j = np.mgrid[0:image.shape[0], 0:image.shape[1]]
    result = masked_image.copy()
    distance = distance[result]
    i = np.ascontiguousarray(i[result], dtype=np.intp)
    j = np.ascontiguousarray(j[result], dtype=np.intp)
    result = np.ascontiguousarray(result, np.uint8)

    # Determine the order in which pixels are processed.
    # We use a random # for tiebreaking. Assign each pixel in the image a
    # predictable, random # so that masking doesn't affect arbitrary choices
    # of skeletons
    #
    generator = np.random.RandomState(0)
    tiebreaker = generator.permutation(np.arange(masked_image.sum()))
    order = np.lexsort((tiebreaker,
                        corner_score[masked_image],
                        distance))
    order = np.ascontiguousarray(order, dtype=np.int32)

    table = np.ascontiguousarray(table, dtype=np.uint8)
    # Remove pixels not belonging to the medial axis
    _skeletonize_loop(result, i, j, order, table)

    result = result.astype(bool)
    if not mask is None:
        result[~mask] = image[~mask]
    if return_distance:
        return result, store_distance
    else:
        return result


def _pattern_of(index):
    """
    Return the pattern represented by an index value
    Byte decomposition of index
    """
    return np.array([[index & 2**0, index & 2**1, index & 2**2],
                     [index & 2**3, index & 2**4, index & 2**5],
                     [index & 2**6, index & 2**7, index & 2**8]], bool)


def _table_lookup(image, table):
    """
    Perform a morphological transform on an image, directed by its
    neighbors

    Parameters
    ----------
    image : ndarray
        A binary image
    table : ndarray
        A 512-element table giving the transform of each pixel given
        the values of that pixel and its 8-connected neighbors.
    border_value : bool
        The value of pixels beyond the border of the image.

    Returns
    -------
    result : ndarray of same shape as `image`
        Transformed image

    Notes
    -----
    The pixels are numbered like this::


      0 1 2
      3 4 5
      6 7 8

    The index at a pixel is the sum of 2**<pixel-number> for pixels
    that evaluate to true.
    """
    #
    # We accumulate into the indexer to get the index into the table
    # at each point in the image
    #
    if image.shape[0] < 3 or image.shape[1] < 3:
        image = image.astype(bool)
        indexer = np.zeros(image.shape, int)
        indexer[1:, 1:]   += image[:-1, :-1] * 2**0
        indexer[1:, :]    += image[:-1, :] * 2**1
        indexer[1:, :-1]  += image[:-1, 1:] * 2**2

        indexer[:, 1:]    += image[:, :-1] * 2**3
        indexer[:, :]     += image[:, :] * 2**4
        indexer[:, :-1]   += image[:, 1:] * 2**5

        indexer[:-1, 1:]  += image[1:, :-1] * 2**6
        indexer[:-1, :]   += image[1:, :] * 2**7
        indexer[:-1, :-1] += image[1:, 1:] * 2**8
    else:
        indexer = _table_lookup_index(np.ascontiguousarray(image, np.uint8))
    image = table[indexer]
    return image
