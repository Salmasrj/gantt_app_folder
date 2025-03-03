#!/bin/bash
apt-get update
apt-get install -y graphviz

pip install librairie/grapheMPM-0.7.2-py3-none-any.whl
sed -i 's/from numpy import asarray, prod, float_, round, floor, uint8/from numpy import asarray, prod, float16, round, floor, uint8/' $(python -c "import site; print(site.getsitepackages()[0])")/grapheMPM/__init__.py
