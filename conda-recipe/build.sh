#!/bin/bash

$PYTHON setup.py install
DIR=`$PYTHON -c 'from __future__ import print_function;import vistrails.core.system; print(vistrails.core.system.packages_directory())'`
cp -r vt_config/NSLS-II $DIR
