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

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import six
import os
import shutil
import sys
from sys import platform as _platform
from subprocess import call


# function to get user input (yes/no) on a question
# function was found: http://code.activestate.com/recipes/577058/
# and is available under the MIT license
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def make_symlink(dst, src):
    # todo check for the presence of ~/.vistrails/userpackages
    # clear out any existing stuff in the userpackages/NSLS-II folder
    """
    turns out that you can't check for the presence of symlinks in windows at all.
    http://stackoverflow.com/questions/15258506/os-path-islink-on-windows
    -with-python
    """

    # from subprocess import call
    if os.path.islink(dst):
        # unlink it
        os.unlink(dst)
        print('unlinked: {0}'.format(dst))
    elif _platform == 'win32':
        # you're on windows and os.path.islink alwasys reports False in py2.7
        # http://stackoverflow.com/questions/15258506/os-path-islink-on-windows-with-python
        # assume that this is a symbolic link
        ret = call(['rmdir', dst], shell=True)
        if ret == 0:
            # NSLS-II was an empty directory or a symlink
            print('NSLS-II was present as an empty directory or a symlink and '
                  'was successfully deleted from {0}'.format(dst))
        if ret == 267 and query_yes_no('Delete the file: {0}?'.format(dst)):
            # 'NSLS-II' is a file
            call(['del', dst], shell=True)
            print('NSLS-II was present as a file and removed from {0}'
                  ''.format(dst))
        elif ret == 145:
            # 'NSLS-II' is not a symlink. os.path.isdir will remove it
            print('NSLS-II is a directory and is not empty. It will be removed '
                  'by os.path.rmtree({0})'.format(dst))
            pass
    # check to see if the folder is still there after attempts
    # to unlink it in linux/mac environs or remove it on windows
    if (os.path.isdir(dst) and
            query_yes_no('Delete the non-empty folder: {0}?'.format(dst))):
        # remove it
        try:
            shutil.rmtree(dst)
            print("Successfully rmtree'd: {0}".format(dst))
        except WindowsError as whee:
            # you're on windows and os.path.islink alwasys reports False in
            # py2.7 according to stack overflow, which we know is always correct
            # http://stackoverflow.com/questions/15258506/os-path-islink-on-windows-with-python
            call(['rmdir', dst], shell=True)
            print("Successfully rmdir'd: {0}".format(dst))
    elif (os.path.isfile(dst) and
          query_yes_no('Delete the file: {0}?'.format(dst))):
        # remove it
        os.remove(dst)
        print("Successfully os.remove'd: {0}".format(dst))
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
        call(['mklink', '/j', dst, src], shell=True)