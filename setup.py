#!/usr/bin/env python
"""
  Setup properties that work for pip install, which also works with conda.
    `pip install -e .` will link this source tree with a python environment
    for development.

    @see README.md for more details
"""

from setuptools import setup

DESCRIPTION = """
  auto-cli-py
  Python Package to automatically create CLI from function via introspection
"""

setup(
  name='auto-cli-py',
  version='0.4.2',
  description=DESCRIPTION,
  url='http://github.com/tangledpath/auto-cli-py',
  author='Steven Miers',
  author_email='steven.miers@gmail.com',
  include_package_data=True,
  license='copyright',
  packages=['auto_cli'],
  tests_require=[],
  zip_safe=False
)
