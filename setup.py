#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
import strconv

setup(name='strconv',
      version=strconv.__version__,
      author='Byron Ruth',
      author_email='b@devel.io',
      description='String type inference and conversion',
      license='BSD',
      url='https://github.com/mcobzarenco/strconv',
      test_suite='test_strconv',
      install_requires=[
          'python-dateutil>=2.2',
      ],
      py_modules=['strconv'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
      ],
)
