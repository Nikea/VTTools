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

from __future__ import (absolute_import, division, print_function,
                        )

import six
import logging
logger = logging.getLogger(__name__)

from nose.tools import assert_true
from skxray.testing.decorators import known_fail_if
from vttools.utils import make_symlink, query_yes_no
import tempfile
import os
import shutil
from subprocess import call
from vttools import wrap_lib
import numpy as np
from numpy import interp
from numpy.testing import assert_string_equal, assert_equal, assert_raises


def test_obj_src():
    string_result = wrap_lib.obj_src(interp)
    initial_txt_should_be = str('def interp(x, xp, fp, left=None, right=None)')
    initial_txt_actual = string_result[0:44]
    assert_string_equal(initial_txt_actual, initial_txt_should_be)


def test_pytype_to_vtsig():
    docstring_type_list = ('ndarray', 'array', 'array_like', 'np.ndarray',
                           'list', 'int', 'integer', 'scalar', 'float',
                           'tuple', 'dict', 'bool', 'str', 'string',
                           'numpy.dtype', 'np.dtype', 'dtype', 'sequence')
    for _ in docstring_type_list:
        param_type = _
        param_name = 'test_' + _
        assert_equal(wrap_lib.pytype_to_vtsig(param_type, param_name),
                            wrap_lib.sig_map[param_type])

def test_pytype_to_vtsig_error():
    param_name = 'FSM'
    param_type = 'outer_space'
    assert_raises(ValueError, wrap_lib.pytype_to_vtsig, param_type, param_name)


def test_type_optional():
    test_string1 = 'array, optional'
    test_string2 = 'array'
    assert_equal(wrap_lib._type_optional(test_string1)[1], True)
    assert_equal(wrap_lib._type_optional(test_string2)[1], False)


def test_enum_type():
    """
    Example function docstrings:
    1) numpy.linalg.svd()
        Parameters :
            a : (..., M, N) array_like
                A real or complex matrix of shape (M, N) .
            full_matrices : bool, optional
                If True (default), u and v have the shapes (M, M) and (N, N),
                respectively. Otherwise, the shapes are (M, K) and (K, N),
                respectively, where K = min(M, N).
            compute_uv : bool, optional
                Whether or not to compute u and v in addition to s. True by
                default.
        Returns :
            u : { (..., M, M), (..., M, K) } array
                Unitary matrices. The actual shape depends on the value of
                full_matrices. Only returned when compute_uv is True.
            s : (..., K) array
                The singular values for every matrix, sorted in descending
                order.
            v : { (..., N, N), (..., K, N) } array
                Unitary matrices. The actual shape depends on the value of
                full_matrices. Only returned when compute_uv is True.
    """
    test_str1 = '{True, False, Maybe}'
    test_str2 = 'array'
    test_str3 = '{true, FALSE, 452}'
    test_str4 = '{12.5, 5.3}'
    test_str5 = '{ (..., M, M), (..., M, K) } array'
    test_str6 = '{ (..., N, N), (..., K, N) } array'
    assert_equal(wrap_lib._enum_type(test_str1)[1], True)
    assert_equal(wrap_lib._enum_type(test_str1)[2], ['True', 'False',
                                                    'Maybe'])
    assert_equal(wrap_lib._enum_type(test_str2)[1], False)
    assert_raises(ValueError, wrap_lib._enum_type, test_str3)
    assert_raises(ValueError, wrap_lib._enum_type, test_str4)
    assert_equal(wrap_lib._enum_type(test_str5)[1], True)
    assert_equal(wrap_lib._enum_type(test_str6)[1], True)


def test_sized_array():
    """
    Example function docstrings:
    1)  numpy.outer()
       Parameters :
        a : (M,) array_like
            First input vector. Input is flattened if not already
            1-dimensional.
        b : (N,) array_like
            Second input vector. Input is flattened if not already
            1-dimensional.
        Returns :
        out : (M, N) ndarray
    2) numpy.linalg.svd()
        Parameters :
            a : (..., M, N) array_like
                A real or complex matrix of shape (M, N) .
            full_matrices : bool, optional
                If True (default), u and v have the shapes (M, M) and (N, N),
                respectively. Otherwise, the shapes are (M, K) and (K, N),
                respectively, where K = min(M, N).
            compute_uv : bool, optional
                Whether or not to compute u and v in addition to s. True by
                default.
        Returns :
            u : { (..., M, M), (..., M, K) } array
                Unitary matrices. The actual shape depends on the value of
                full_matrices. Only returned when compute_uv is True.
            s : (..., K) array
                The singular values for every matrix, sorted in descending
                order.
            v : { (..., N, N), (..., K, N) } array
                Unitary matrices. The actual shape depends on the value of
                full_matrices. Only returned when compute_uv is True.
    """
    #This string should be stripped and assigned as a basic array
    test_str1 = '(N, M, P) array' #PASS
    test_str2 = '(..., K) array' #PASS
    test_str3 = '(..., M, N) array_like' #PASS
    test_str4 = '(N, M, P) ndarray' #PASS
    #This string should pass through this function without processing
    # or modification (should pass through unscathed)
    test_str5 = '(N M, P) ndarray' #FAIL
    test_str6 = 'ndarray' #FAIL
    test_str7 = '(M,) array_like' #PASS
    test_str8 = '(M) array_like' #PASS

    assert_equal(wrap_lib._sized_array(test_str1), 'array')
    assert_equal(wrap_lib._sized_array(test_str2), 'array')
    assert_equal(wrap_lib._sized_array(test_str3), 'array')
    assert_equal(wrap_lib._sized_array(test_str4), 'array')
    assert_equal(wrap_lib._sized_array(test_str5), '(N M, P) ndarray')
    assert_equal(wrap_lib._sized_array(test_str6), 'ndarray')
    assert_equal(wrap_lib._sized_array(test_str7), 'array')
    assert_equal(wrap_lib._sized_array(test_str8), 'array')


def test_check_alt_types():
    test_str1 = 'float or int'
    test_str2 = 'scalar or tuple of scalars'
    test_str3 = 'int or scalar'
    test_str4 = 'scalar or sequence of scalars'
    test_str5 = 'MxN ndarray'
    test_str6 = 'integer value'

    assert_equal(wrap_lib._check_alt_types(test_str1), 'float')
    assert_equal(wrap_lib._check_alt_types(test_str2), 'tuple')
    assert_equal(wrap_lib._check_alt_types(test_str3), 'scalar')
    assert_equal(wrap_lib._check_alt_types(test_str4), 'list')
    assert_equal(wrap_lib._check_alt_types(test_str5), 'ndarray')
    assert_equal(wrap_lib._check_alt_types(test_str6), 'int')


def test_truncate_description():
    original_description1 = ['length of three']
    original_description2 = ['This object is the original description ' \
                           'stripped from the doc string. The object is ',
                           'actually a list of strings.']
    word_count = 6
    #Test to make sure descriptions that are smaller than the
    # specified word count pass through correctly
    assert_equal(wrap_lib._truncate_description(original_description1,
                                                word_count),
                 'length of three')
    #Test that function descriptions less than word_count are cropped and
    # passed through correctly
    assert_equal(wrap_lib._truncate_description(original_description2,
                                                word_count),
                 'This object is the original description')



def test_guess_type():
    """
    The function _guess_type() is used in the function _enum_type(). The
    initial input is the stripped type string.
    e.g. {14, 0.333, 5j, True, False, Maybe}
    The input string is then checked to make sure that there are enclosing
    curly braces, after which the enum string is separated out using the
    commas, any string declarations are then removed (i.e. ' or "), and each
    element of the original enum string is converted to an element of a list
    of strings. Each of these separated elements are then entered into the
    _guess_type() function.

    All of these test strings are parameter types that should be caught and
    evaluated using the _guess_type() function.
    """
    test_1 = '0.333'
    test_2 = '14'
    test_3 = '5j'
    test_4 = 'False'
    test_5 = 'Volume'
    assert_equal(wrap_lib._guess_type(test_1), 'float')
    assert_equal(wrap_lib._guess_type(test_2), 'int')
    assert_equal(wrap_lib._guess_type(test_3), 'complex')
    assert_equal(wrap_lib._guess_type(test_4), 'str') #Not sure how to get
                                                      # this to eval to bool
    assert_equal(wrap_lib._guess_type(test_5), 'str')




def test_define_input_ports():
    pass


def test_define_output_ports():
    pass


def test_gen_module():
    pass


def test_wrap_function():
    pass


def test_wrap_class():
    pass

if __name__ == '__main__':
    test_obj_src()
    test_pytype_to_vtsig()
    test_pytype_to_vtsig_error()
    test_type_optional()
    test_enum_type()
    test_sized_array()
    test_check_alt_types()
    test_truncate_description()
    test_guess_type()
    # no-op, for now
    test_define_input_ports()
    test_define_output_ports()
    test_gen_module()
    test_wrap_function()
    test_wrap_class()
