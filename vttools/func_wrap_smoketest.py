# ######################################################################
# Copyright (c) 2014, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
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
This module is for spectroscopy specific tools (spectrum fitting etc).
"""
from __future__ import (absolute_import, division, print_function,
                        )

import six
from six.moves import zip
import numpy as np
import logging
logger = logging.getLogger(__name__)


def func_wrap_smoke_test(param_str, param_ndarray, param_int, param_float,
                         param_list, param_dict):
    """Function wrapping test. Makes sure the smoke doesn't leak out

    The function prints the input parameters and then returns them in
    the same order

    Parameters
    ----------
    param_str : str
        Test param that should be a string
    param_ndarray : np.ndarray
        Test param that should be a numpy array
    param_int : int
        Test param that should be an integer
    param_float : float
        Test param that should be a float
    param_list : list
        Test param that should be a list
    param_dict : dict
        Test param that should be a dict

    Returns
    -------
    param_str : str
        Test param that should be a string
    param_ndarray : np.ndarray
        Test param that should be a numpy array
    param_int : int
        Test param that should be an integer
    param_float : float
        Test param that should be a float
    param_list : list
        Test param that should be a list
    param_dict : dict
        Test param that should be a dict
    """

    print('param_str: {0}'.format(param_str))
    print('param_ndarray: {0}'.format(param_ndarray))
    print('param_int: {0}'.format(param_int))
    print('param_float: {0}'.format(param_float))
    print('param_list: {0}'.format(param_list))
    print('param_dict: {0}'.format(param_dict))
    print('param_str: {0}'.format(param_str))

    return (param_str, param_ndarray, param_int,
            param_float, param_list, param_dict)
