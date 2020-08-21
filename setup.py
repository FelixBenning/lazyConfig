#!/usr/bin/env python

from distutils.core import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='lazyConfig',
      version='0.1',
      author='Felix Benning',
      author_email='felix.benning@gmail.com',
      description='lazily loading and overriding configuration for the lazy coder',
      long_description=long_description,
      url='https://github.com/FelixBenning/lazyConfig',
      packages=['lazyConfig' ],
      classifiers=[
            "Programming Language :: Python :: 3"
            "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"
            "Development Status :: 4 - Beta"
      ]
     )