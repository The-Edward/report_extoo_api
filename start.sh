#!/bin/bash

PY="python3"
DIR="/var/www/ipoo"
VENV="/var/www/ipoo/venv"
SCRIPT="runner.py"
PARAMS=""

cd $DIR
${VENV}/bin/${PY} ${SCRIPT} "${PARAMS}"
