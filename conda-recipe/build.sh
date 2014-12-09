#!/bin/bash

$PYTHON setup.py install
cp -r vt_config/NSLS-II $SP_DIR/vistrails/packages/
