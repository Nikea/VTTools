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
'''
Created on Apr 29, 2014
'''
from __future__ import (absolute_import, division, print_function,
                        )
import six
import logging

import traceback
import importlib
import collections

from vttools import wrap_lib, scrape
from vttools.vtmods.import_lists import load_config

logger = logging.getLogger(__name__)

# get modules to import
import_dict = load_config()

_black_list = ['who', 'mafromtxt', 'ndfromtxt', 'source',
                 'info', 'add_newdoc_ufunc', 'frombuffer',
                 'fromiter', 'frompyfunc', 'getbuffer',
                 'newbuffer', 'pkgload', 'recfromcsv',
                 'recfromtxt', 'savez', 'savez_compressed',
                 'set_printoptions', 'seterrcall', 'tensordot',
                 'genfromtxt', 'ppmt', 'pv', 'rate', 'nper', 'fv',
                 'ipmt', 'issubclass_', 'pmt', 'formatter',
                 # skxray
                 'peak_refinement']

_exclude_markers = ['busday', 'buffer']


def get_modules():

    # autowrap classes
    # class_list = import_dict['autowrap_classes']
    # vtclasses = [wrap_lib.wrap_function(**func_dict)
    #              for func_dict in class_list]

    # import the hand-built VisTrails modules
    module_list = import_dict['import_modules']
    pymods = [importlib.import_module(module_name, module_path)
              for module_path, mod_lst in six.iteritems(module_list)
              for module_name in mod_lst]

    vtmods = [vtmod for mod in pymods for vtmod in mod.vistrails_modules()]

    vtfuncs = []
    mod_targets = ['numpy',
                   'numpy.fft',
                   'numpy.polynomial',
                   'numpy.random',
                   'scipy',
                   'scipy.cluster',
                   'scipy.fftpack',
                   'scipy.integrate',
                   'scipy.interpolate',
                   'scipy.io',
                   'scipy.linalg',
                   'scipy.misc',
                   'scipy.ndimage',
                   'scipy.odr',
                   'scipy.optimize',
                   'scipy.signal',
                   'scipy.sparse',
                   'scipy.spatial',
                   'scipy.special',
                   'scipy.stats',
                   'skxray.calibration',
                   'skxray.core',
                   'skxray.recip',
                   'skxray.io.binary',
                   'skxray.api.diffraction',
                   'vttools.to_wrap.fitting',
                   ]

    for mod_name in mod_targets:
        print('=' * 25)
        print('starting module {}'.format(mod_name))
        print('=' * 25)
        mod_specs = scrape.scrape_module(mod_name,
                                         black_list=_black_list,
                                         exclude_markers=_exclude_markers)
        for ftw, spec_dict in six.iteritems(mod_specs):
            try:
                tmp = wrap_lib.wrap_function(**spec_dict)
                vtfuncs.append(tmp)
            except Exception as e:
                logger.warn("%s failed wrapping on %s.%s",
                        e, mod_name, ftw)

    all_mods = vtmods + vtfuncs
    if len(all_mods) != len(set(all_mods)):
        raise ValueError('Some modules have been imported multiple times.\n'
                         'Full list: {0}'
                         ''.format([x for x, y in
                                    collections.Counter(all_mods).items()
                                    if y > 1]))

    # return the valid VisTrails modules
    return all_mods


# # init the modules list
_modules = get_modules()
