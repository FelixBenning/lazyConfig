#!/bin/sh
set -e
python setup.py sdist bdist_wheel
python -m twine upload dist/*