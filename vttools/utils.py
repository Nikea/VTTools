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
                        print_function, )
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


def make_symlink(dst, src, silently_move=False):
    """Helper function used to make symlinks.

    Will delete existing folder/file/folder tree in the destination location

    Parameters
    ----------
    dst : str
        Destination for symlink
    src : str
        Source for symlink
    silently_destroy : bool, optional
        False: Prompt user if they would like to remove a file or file tree if
               one is found at 'dst'
        True: Silently delete folder tree or file if it is found at 'dst'

    Returns
    -------
    success : bool
        Flag denoting the success or failure of the symlink creation

    Note
    ----
    turns out that you can't check for the presence of symlinks in windows at all.
    http://stackoverflow.com/questions/15258506/os-path-islink-on-windows
    -with-python
    """
    dst_dir = os.path.dirname(dst.rstrip(os.path.sep))
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    # get a temporary directory
    if os.path.exists(dst):
        if silently_move or (((os.path.isfile(dst) or (os.path.isdir(dst)) and
                             query_yes_no('Move NSLS-II from userpackages?')))):
            import tempfile
            temp_dir = tempfile.mkdtemp()
            shutil.move(dst, temp_dir)
            print('Previous NSLS-II folder moved to {0}'.format(temp_dir))
        else:
            print('NSLS-II already exists in userpackages. Please move or delete it'
                  'and then re-run setup.py')
            return False

    # this symlink does not get removed when pip uninstall vttools is run...
    # todo figure out how to make pip uninstall remove this symlink
    try:
        # symlink the NSLS-II folder into userpackages
        os.symlink(src, dst)
    except AttributeError:
        # you must be on Windows!
        call(['mklink', '/j', dst, src], shell=True)

    return True
