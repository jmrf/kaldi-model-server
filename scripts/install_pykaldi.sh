#!/bin/bash

set -o pipefail

WHEEL_NAME=pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl

wget https://ltdata1.informatik.uni-hamburg.de/pykaldi/$WHEEL_NAME
pip install $WHEEL_NAME

rm $WHEEL_NAME

