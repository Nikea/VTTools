# ######################################################################
# Copyright (c) 2014, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
#                                                                      #
# @author: Li Li (lili@bnl.gov)                                        #
# created on 07/10/2014                                                #
#                                                                      #
# Original code:                                                       #
# @author: Mirna Lerotic, 2nd Look Consulting                          #
#         http://www.2ndlookconsulting.com/                            #
# Copyright (c) 2013, Stefan Vogt, Argonne National Laboratory         #
# All rights reserved.                                                 #
#                                                                      #
# Redistribution and use in source and binary forms, with or without   #
# modification, are permitted provided that the following conditions   #
# are met:                                                             #
#                                                                      #
# * Redistributions of source code must retain the above copyright     #
#   notice, this list of conditions and the following disclaimer.      #
#                                                                      #
# * Redistributions in binary form must reproduce the above copyright  #
#   notice this list of conditions and the following disclaimer in     #
#   the documentation and/or other materials provided with the         #
#   distribution.                                                      #
#                                                                      #
# * Neither the name of the Brookhaven Science Associates, Brookhaven  #
#   National Laboratory nor the names of its contributors may be used  #
#   to endorse or promote products derived from this software without  #
#   specific prior written permission.                                 #
#                                                                      #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS  #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT    #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS    #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE       #
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,           #
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES   #
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR   #
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)   #
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,  #
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OTHERWISE) ARISING   #
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                          #
########################################################################
"""
This module creates a namespace for Full-Field Imaging and Image Processing
"""


import logging
logger = logging.getLogger(__name__)
import skimage.filter as sk
#import skimage.filter.threshold_adaptive as thresh_adapt

#-----------------------------------------------------------------------------
#Image processing: Image thresholding
#-----------------------------------------------------------------------------
from skxray.core.thresholding import (thresh_globalGT,
                                       thresh_globalLT,
                                       thresh_bounded,
                                       thresh_otsu,
                                       thresh_yen,
                                       thresh_isodata)


def thresh_adapt(src_data, kernel_size, filter_type='gaussian'):
    """
    Applies an adaptive threshold to the source data set.
    Parameters
    ----------
    src_data : ndarray
        Source data on which to apply the threshold algorithm
    kernel_size : integer
        Specify kernel size for automatic thresholding operation
        Note: Value must be an odd valued integer
    filter_type : string
        Filter type options:
            method : {'generic', 'gaussian', 'mean', 'median'}, optional
            Method used to determine adaptive threshold for local
            neighbourhood in weighted mean image.
            * 'generic': use custom function (see `param` parameter)
            * 'gaussian': apply gaussian filter (see `param` parameter
                for custom sigma value)
            * 'mean': apply arithmetic mean filter
            * 'median': apply median rank filter
    Returns
    -------
    output_data : ndarray
        The function returns a binary array where all voxels with values equal
        to 1 correspond to voxels within the identified threshold range.
    """

    if type(kernel_size) != int:
        raise TypeError('Specified value for kernel_size is not an integer!')
    if (kernel_size % 2) == 0:
        raise ValueError('Specified kernel_size value is not an odd valued '
                         'integer!')
    output_data = sk.threshold_adaptive(src_data, kernel_size, filter_type,
                                        offset=0, param=None)
    return output_data

__all__ = ['thresh_adapt', 'thresh_bounded', 'thresh_globalGT',
           'thresh_globalLT', 'thresh_isodata', 'thresh_otsu', 'thresh_yen']

thresh_adapt.k_shape = ['2D', '3D']
thresh_adapt.filter_type = ['generic', 'gaussian', 'mean', 'median']
