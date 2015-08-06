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

import numpy as np
from scipy import ndimage
import logging
logger = logging.getLogger(__name__)

#-----------------------------------------------------------------------------
#Image processing: Image transformation
#-----------------------------------------------------------------------------

def swap_axes(src_data, select_axes):
    """
    This function allows for volume adjustment and rearrangement by providing
    the ability to swap volume axes.

    Parameters
    ----------
    src_data : ndarray
        Identify source data for modification

    select_axes : string
        Identify the axis pair for the operation.
        Options:
            "XY" -- Swap X and Y axes
            "YZ" -- Swap Y and Z axes
            "XZ" -- Swap X and Z axes
    Returns
    -------
    output : ndarray
        Return operation result to specified variable
    """
    if select_axes == 'XY':
        output = np.swapaxes(src_data, 2, 1)
    elif select_axes == 'YZ':
        output = np.swapaxes(src_data, 1, 0)
    elif select_axes == 'XZ':
        output = np.swapaxes(src_data, 2, 0)
    return output


def flip_axis(src_data, flip_direction):
    """
    This function allows for volume adjustment and rearrangement by providing
    the ability to flip along a given volume axes.

    Parameters
    ----------
    src_data : ndarray
        Identify source data for modification

    flip_direction : string
        Identify the axis along which to flip.
        Options:
            "Flip X" -- Flip X and Y axes
            "Flip Y" -- Swap Y and Z axes
            "Flip Z" -- Swap X and Z axes

    Returns
    -------
    output : ndarray
        Return operation result to specified variable
    """
    if flip_direction == "Flip X":
        output = src_data[..., ..., ::-1]
    elif flip_direction == "Flip Y":
        output = src_data[..., ::-1, ...]
    elif flip_direction == "Flip Z":
        output = src_data[::-1, ..., ...]
    return output


def crop_volume(src_data, x_MIN, x_MAX, y_MIN, y_MAX, z_MIN, z_MAX):
    """
    This function enables the cropping of volume data sets. While this function
    allows changes to be made to volume dimensions, this function does not
    operate, and should not be confused with the resize volume function.

    Parameters
    ----------
    src_data : ndarray
        Identify source data for modification

    x_MIN : int
        X-axis minimum voxel coordinate number

    x_MAX : int
        X-axis maximum voxel coordinate number

    y_MIN : int
        Y-axis minimum voxel coordinate number

    y_MAX : int
        Y-axis maximum voxel coordinate number

    z_MIN : int
        Z-axis minimum voxel coordinate number

    z_MAX : int
        Z-axis maximum voxel coordinate number

    Returns
    -------
    output : ndarray
        Return operation result to specified variable
    """
    output = src_data[z_MAX:z_MIN, y_MAX:y_MIN, x_MAX:x_MIN]
    return output


def rotate_volume(src_data, rotation_axis, rotate_degrees, fill_value):
    """
    This function allows for volume adjustment and rearrangement by rotating a
    data set along a given axix by a fixed number of degrees. After executing
    the rotation, arrays are expanded to include all of the original voxel data.
    As a result, a subsequent cropping step may be required to return a data set
    to its original shape and size.

    Parameters
    ----------
    src_data : ndarray
        Identify source data for modification

    rotation_axis : string
        Specify the axis for rotation
        Options:
            "Z-axis"
            "Y-axis"
            "X-Axis"

    rotate_degrees : int
        Enter the number of degrees for the rotation

    fill_value : float
        identify a value to be assigned to all new voxels created to fill empty
        space generated when the array is expanded as a result of the rotation.

    Returns
    -------
    output : ndarray
        Return operation result to specified variable
    """
    if rotation_axis == 'Z-axis':
        select_axis = (2,1)
    elif rotation_axis == 'Y-axis':
        select_axis = (2,0)
    elif rotation_axis == 'X-axis':
        select_axis = (1,0)
    output = ndimage.rotate(src_data,
                            rotate_degrees,
                            select_axis,
                            reshape=True,
                            cval=fill_value)
    return output

__all__ = ['swap_axes', 'rotate_volume', 'crop_volume', 'flip_axis']

swap_axes.select_axes = ['XY', 'YZ', 'XZ']
flip_axis.flip_direction = ['Flip Z', 'Flip Y', 'Flip X']
rotate_volume.rotate_axis = ['Z-axis', 'Y-axis', 'X-axis']
