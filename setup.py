#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='image2radiomics',
    version='0.8.4',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    scripts=['i2r.py'],
    install_requires=[
        'torch>=2.1.2',
        'numpy<2',
        'pandas>2',
        'SimpleITK',
        'nibabel>=2.3.0',
        'rt_utils',
        'pyradiomics>=3.0.1,<3.2',
        'p-tqdm',
        'dicom2nifti',
        'nnunetv2==2.3.1',
        'TotalSegmentator==2.1.0',
        'opencv-python>=4.9',
        'openpyxl>=3',
        'scikit-learn>1.4,<2',
        'joblib>1.3',
        ],
    entry_points={
    'console_scripts': [
        'i2r=img2radiomics:main',
    ]
    }
)
