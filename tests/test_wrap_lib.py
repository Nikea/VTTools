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
                        unicode_literals)

import six
import logging
logger = logging.getLogger(__name__)

from nose.tools import assert_true
from nsls2.testing.decorators import known_fail_if
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
    initial_txt_should_be = 'def interp(x, xp, fp, left=None, right=None)'
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
    test_str1 = '{True, False, Maybe}'
    test_str2 = 'array'
    test_str3 = '{true, FALSE, 452}'
    test_str4 = '{12.5, 5.3}'
    assert_equal(wrap_lib._enum_type(test_str1)[1], True)
    assert_equal(wrap_lib._enum_type(test_str1)[2], ['True', 'False',
                                                    'Maybe'])
    assert_equal(wrap_lib._enum_type(test_str2)[1], False)
    assert_raises(ValueError, wrap_lib._enum_type, test_str3)
    assert_raises(ValueError, wrap_lib._enum_type, test_str4)

def test_sized_array():
    #This string should be stripped and assigned as a basic array
    test_str1 = 'NxMxP 3D array'
    #This string should pass through this function without processing
    # or modification (should pass through unscathed)
    test_str2 = 'ndarray'

    pass

def test_bad_docstring():
    test_str1 = 'list, array, optional'
    test_str2 = '{int, float, more}'
    #test_str1 should: (1) properly show as optional, but (2) raise
    # exception since includes both list and array as input type.

def test_check_alt_types():
    pass


def test_truncate_description():
    pass


def test_guess_type():
    pass


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



def destroy(path):
    try:
        shutil.rmtree(path)
    except WindowsError as whee:
        call(['rmdir', '/S', path], shell=True)


def test_make_symlink():
    test_loc = os.path.join(os.path.expanduser('~'), 'symlinking_test')
    try:
        os.mkdir(test_loc)
    except WindowsError as whee:
        destroy(test_loc)
        os.mkdir(test_loc)
    src = open
    link_name = 'link'
    src = os.path.join(test_loc, link_name)
    os.mkdir(src)
    os.mkdir(os.path.join(test_loc, 'dst'))
    dst = os.path.join(test_loc, 'dst', link_name)
    # create a temporary file in the target location called `link_name`
    with open(dst, 'w+') as tmp_file:
        tmp_file.write('test')
    assert_true(make_symlink(dst=dst, src=src, silently_move=True))
    destroy(dst)
    # make an empty temporary folder in the target location called `link_name`
    os.mkdir(dst)
    assert_true(make_symlink(dst=dst, src=src, silently_move=True))
    destroy(dst)
    # make a non-empty temporary tree in the target location called `link_name`
    os.mkdir(dst)
    os.mkdir(os.path.join(dst, 'sub_folder'))
    assert_true(make_symlink(dst=dst, src=src, silently_move=True))
    destroy(dst)

    shutil.rmtree(test_loc)
