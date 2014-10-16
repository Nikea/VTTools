#!/usr/bin/env python

import setuptools
from distutils.core import setup, Extension

import numpy as np
import os
import shutil
from subprocess import call
import sys

setup(
    name='vttools',
    version='0.0.x',
    author='Brookhaven National Lab',
    packages=["vttools",
              'vttools.vtmods',
              'vttools.vtmods.import_lists'
              ],
    include_dirs=[np.get_include()],
    package_data = {'vttools.vtmods.import_lists': ['*.yaml']}
    )


src = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vt_config',
                   'NSLS-II')
dst = os.path.join(os.path.expanduser('~'), '.vistrails', 'userpackages',
                   'NSLS-II')

from vttools.utils import make_symlink
make_symlink(dst=dst, src=src)
