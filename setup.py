#!/usr/bin/env python3
"""
Setup script for AI Cycling Coach.
"""
from setuptools import setup, find_packages

setup(
    name="ai-cycling-coach",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cycling-coach=main:main',
            'ai-cycling-coach=main:main',
        ],
    },
)