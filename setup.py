#!/usr/bin/env python
"""
  Setup properties that work for pip install, which also works with conda.
    `pip install -e .` will link this source tree with a python environment
    for development.

    @see README.md for more details
"""

from setuptools import setup

DESCRIPTION = "auto-cli-py: python package to automatically create CLI commands from function via introspection"

long_description = []
with open("README.md", "r") as fh:
  long_description.append(fh.read())

long_description.append("---")
long_description.append("---## Example")
long_description.append("```python")
with open("examples.py", "r") as fh:
  long_description.append(fh.read())
long_description += "```"

setup(
  name='auto-cli-py',
  version='0.4.6',
  description=DESCRIPTION,
  url='http://github.com/tangledpath/auto-cli-py',
  author='Steven Miers',
  author_email='steven.miers@gmail.com',
  include_package_data=True,
  long_description="\n".join(long_description),
  long_description_content_type="text/markdown",
  packages=['auto_cli'],
  python_requires='>=3.6',
  tests_require=[],
  zip_safe=False,
  classifiers=[
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
  ],
)
