#!/usr/bin/env python

import setuptools
from distutils.core import setup, Extension
from setupext import ext_modules
import numpy as np
import os
import shutil
from subprocess import call

setup(
    name='vttools',
    version='0.0.x',
    author='Brookhaven National Lab',
    packages=["vttools",
              'vttools.vtmods'
              ],
    include_dirs=[np.get_include()],
    ext_modules=ext_modules
    )

# this_file_loc = os.path.realpath(__file__)
src = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vt_config',
                   'NSLS-II')
dst = os.path.join(os.path.expanduser('~'), '.vistrails', 'userpackages',
                   'NSLS-II')

print('src: {0}'.format(src))
print('dst: {0}'.format(dst))
# todo check for the presence of ~/.vistrails/userpackages
# clear out any existing stuff in the userpackages/NSLS-II folder
"""
turns out that you can't check for the presence of symlinks in windows at all.
http://stackoverflow.com/questions/15258506/os-path-islink-on-windows
-with-python
"""
from sys import platform as _platform

if os.path.islink(dst):
    # unlink it
    os.unlink(dst)
    print('unlinked: {0}'.format(dst))
elif _platform == 'win32':
    # you're on windows and os.path.islink alwasys reports False in py2.7
    # http://stackoverflow.com/questions/15258506/os-path-islink-on-windows-with-python
    # assume that this is a symbolic link
    call(['rmdir', dst], shell=True)
elif os.path.isdir(dst):
    # remove it
    try:
        shutil.rmtree(dst)
        print("rmtree'd: {0}".format(dst))
    except WindowsError as whee:
        # you're on windows and os.path.islink alwasys reports False in py2.7
        # http://stackoverflow.com/questions/15258506/os-path-islink-on-windows-with-python
        call(['rmdir', dst], shell=True)
        print("rmdir'd: {0}".format(dst))
elif os.path.isfile(dst):
    # remove it
    os.remove(dst)
    print("os.remove'd: {0}".format(dst))
else:
    # the file probably doesn't exist
    pass

# this symlink does not get removed when pip uninstall vttools is run...
# todo figure out how to make pip uninstall remove this symlink
try:
    # symlink the NSLS-II folder into userpackages
    os.symlink(src, dst)
except AttributeError as ae:
    # you must be on Windows!
    from subprocess import call
    call(['mklink', '/j', dst, src], shell=True)

# shutil.copytree(src, dst, symlinks=True)
# osos.path.expanduser('~/')