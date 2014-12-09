
import setuptools
from distutils.core import setup

setup(
    name='vttools',
    version='0.0.x',
    author='Brookhaven National Lab',
    packages=["vttools",
              'vttools.vtmods',
              'vttools.vtmods.import_lists',
              'vttools.to_wrap'
              ],
    package_data = {'vttools.vtmods.import_lists': ['*.yaml']}
    )
