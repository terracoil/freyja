#!/bin/bash
find . -name *.pyc | xargs rm -r
find . -name __pycache__ | xargs rm -r
find . -name .ipynb_checkpoints | xargs rm -r
find . -name .pytest_cache | xargs rm -r
rm -rf build
rm -rf dist
