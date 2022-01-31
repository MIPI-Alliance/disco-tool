#  ------------------------------------------------------------------------------
#
#  Copyright 2022, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    Setup.py
#
#  Abstract:
#
#    Setup file for package creation.
#
#  -------------------------------------------------------------------------------

from setuptools import setup, find_packages
import pathlib
import site
import sys

here = pathlib.Path(__file__).parent.resolve()

print(site.USER_BASE)
if 'install' in sys.argv:
	print(sys.argv)

from pkg_resources import Requirement, resource_filename
import os
import shutil
setup(
    name='DisCo',
    version='1.0.0',
    description='DisCo Tool',
    url='https://github.com/MIPI-Alliance/private-disco-tool',
    author='Kondal Purma',
    author_email='kondal.r.purma@intel.com',  # Optional

    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

 
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='MIPI, setuptools, development, Audio, ACPI',

    package_dir={'': 'src'},

    packages=find_packages(where='src'),

    python_requires='>=3.6, <4',

    install_requires=['PyPubSub', 'wxPython'],

    extras_require={  
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    package_data= {'disco': ['images/Stacked.bmp','images/MIPIfavicon.ico']},

    entry_points={ 
        'console_scripts': [
            'disco=disco:main',
        ],
    },
    project_urls={
      
        'Source': 'https://github.com/MIPI-Alliance/private-disco-tool',
    },
)
