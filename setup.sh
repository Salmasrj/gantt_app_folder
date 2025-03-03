#!/bin/bash
apt-get update
apt-get install -y graphviz
py -3 -m pip install grapheMPM-0.7.2-py3-none-any.whl
