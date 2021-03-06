#! /usr/bin/env python

import os
import glob

from setuptools import setup, find_packages
from distutils.command.install import install as DistutilsInstall

long_desc=open("README.md").read(),

try:
    #Try and convert the readme from markdown to pandoc
    from pypandoc import convert
    long_desc = convert("README.md", 'rst')
except:
    pass

setup( 
    name='nysa-prometheus-platform',
    version='0.1.0',
    description='Prometheus platform for Nysa',
    author='Cospan Design',
    author_email='user@example.com',
    packages=find_packages('.'),
    url="http://example.com",
    package_data={'' : ["*.json"]},
    install_requires = [
        "nysa"
    ],
    include_package_data = True,
    long_description=long_desc,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
    ],
    keywords="FPGA",
    license="GPL"
)
