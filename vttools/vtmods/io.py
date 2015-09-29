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
from vistrails.core.modules.vistrails_module import (Module, ModuleSettings,
                                                     ModuleError)
from vistrails.core.modules.config import IPort, OPort
from tifffile import imread
from skxray.io.binary import read_binary
import numpy as np
import os
import glob

import logging
logger = logging.getLogger(__name__)


class ReadNumpy(Module):
    _settings = ModuleSettings(namespace="io")
    _input_ports = [
        IPort(name="file", label="File to read in",
              signature="basic:List")
    ]
    _output_ports = [
        OPort(name="data", signature="basic:List")
    ]

    def compute(self):
        fnames = self.get_input('file')
        data = []
        data = [np.load(fname + '.npy') for fname in fnames]
        self.set_output('data', data)


class ReadTiff(Module):
    _settings = ModuleSettings(namespace="io")

    _input_ports = [
        IPort(name="files", label="List of files",
              signature="basic:List"),
    ]

    _output_ports = [
        OPort(name="data", signature="basic:List")
    ]

    def compute(self):
        files_list = self.get_input("files")
        data_list = []
        for file in files_list:
            data_list.append(imread(file))
        self.set_output("data", data_list)

class FindData(Module):
    _settings = ModuleSettings(namespace="io")

    _input_ports = [
        IPort(name="file name", label="file name and extension to search for",
              signature="basic:String"),
        IPort(name="seed path", label="path corresponding to the "
                                      "search starting point. Defaults to "
                                      "the user's home directory.",
              default="~", signature="basic:String"),
    ]

    _output_ports = [
        OPort(name="file path", signature="basic:String")
    ]

    def compute(self):
        seed_path = self.get_input("seed path")
        file_name = self.get_input("file name")
        print file_name
        existing_files = []
        #existing_files = [y for dir_tree in os.walk(os.path.expanduser("~/dev/my_src/")) for y in glob(os.path.join(x[0], 'data.h5'))]
        for dir_tree in os.walk(os.path.expanduser(seed_path)):
            if file_name in dir_tree[2]:
                existing_files.append(os.path.join(dir_tree[0], file_name))
        print existing_files

        for path in existing_files:
            if 'Demos' in path:
                file_path = path
        print file_path

        #existing_file_list = [files for folder in os.walk(os.path.expanduser(
        #    seed_path)) for file in glob(os.path.join(folder[0], fname))]
        #file_path = None
        #print existing_file_list
        #for path in existing_file_list:
        #    if 'Demos' in path:
        #        file_path = path
        #if file_path == None:
        #    if len(existing_file_list) != 0:
        #        file_path = existing_file_list[0]
        #    else:
        #        raise ValueError("File not found.")
        #print file_path
        self.set_output("file path", file_path)



def vistrails_modules():
    return [ReadTiff, ReadNumpy, FindData]
