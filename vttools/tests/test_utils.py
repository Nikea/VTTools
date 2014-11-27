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
from skxray.testing.decorators import known_fail_if, skip_if
from vttools.utils import make_symlink, query_yes_no
import tempfile
import os
import shutil
from subprocess import call


def destroy(path):
    try:
        shutil.rmtree(path)
    except WindowsError as whee:
        call(['rmdir', '/S', path], shell=True)


@skip_if(not os.name == 'nt', 'not on window')
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
