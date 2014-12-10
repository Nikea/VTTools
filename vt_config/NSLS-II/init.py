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
import sys

import importlib
import collections

from vttools import wrap_lib
from vttools.vtmods.import_lists import load_config
from vttools.wrap_lib import AutowrapError

import numpy

logger = logging.getLogger(__name__)

# get modules to import
import_dict = load_config()


def get_modules():
    # set defaults
    try:
        # import the hand-built VisTrails modules
        module_list = import_dict['import_modules']
        pymods = [importlib.import_module(module_name, module_path)
                  for module_path, mod_lst in six.iteritems(module_list)
                  for module_name in mod_lst]
        # autowrap functions
        func_list = import_dict['autowrap_func']
        vtfuncs = []
        for func_dict in func_list:
            try:
                tmp = wrap_lib.wrap_function(**func_dict)
                vtfuncs.append(tmp)
            except Exception as e:
                print('*' * 25)
                print('failed on {}'.format(func_dict))
                print(e)
                print('*' * 25)

        # autowrap classes
        # class_list = import_dict['autowrap_classes']
        # vtclasses = [wrap_lib.wrap_function(**func_dict)
        #              for func_dict in class_list]
    except ImportError as ie:
        msg = ('importing {0} failed\nOriginal Error: {1}'
               ''.format(module_name, module_path, ie))
        print(msg)
        logging.error(msg)
        six.reraise(*sys.exc_info())
    except AutowrapError as ae:
        msg = ('autowrapping {0} failed\nOriginal Error: {1}'
               ''.format(func_dict, ae))
        print(msg)
        logging.error(msg)
        six.reraise(*sys.exc_info())

    vtmods = [vtmod for mod in pymods for vtmod in mod.vistrails_modules()]

    np_black_list = ['who', 'mafromtxt', 'ndfromtxt', 'source', 'info', 'add_newdoc_ufunc',
                     'frombuffer', 'fromiter', 'frompyfunc', 'getbuffer', 'newbuffer', 'pkgload',
                     'recfromcsv', 'recfromtxt', 'savez', 'savez_compressed', 'set_printoptions',
                     'seterrcall', 'tensordot', 'genfromtxt', 'ppmt', 'pv', 'rate', 'nper', 'fv',
                     'ipmt'
                     ]


    funcs_to_wrap = [atr_name for atr_name, atr in
                     ((atr_name, getattr(numpy, atr_name)) for atr_name in dir(numpy)
                      if not (atr_name.startswith('_') or 'busday' in atr_name or
                              atr_name in np_black_list))
                      if callable(atr) and type(atr) is not type]

    numpy_mods = []
    for ftw in funcs_to_wrap:
        try:
            tmp = wrap_lib.wrap_function(ftw, 'numpy')
            numpy_mods.append(tmp)
        except Exception as e:
            print('*' * 25)
            print('failed on {}'.format(ftw))
            print(e)
            print('*' * 25)


    all_mods = vtmods + vtfuncs  + numpy_mods  # + vtclasses
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
