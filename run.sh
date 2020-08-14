#!/bin/bash

# Ensure we're in the MusicBot directory
cd "$(dirname "$BASH_SOURCE")"

# Set variables for python versions. Could probably be done cleaner, but this works.
declare -A python=( ["0"]=`python -c 'import sys; version=sys.version_info[:3]; print("{0}".format(version[0]))' || { echo "no py"; }` ["1"]=`python -c 'import sys; version=sys.version_info[:3]; print("{0}".format(version[1]))' || { echo "no py"; }` ["2"]=`python -c 'import sys; version=sys.version_info[:3]; print("{0}".format(version[2]))' || { echo "no py"; }` )
declare -A python3=( ["0"]=`python3 -c 'import sys; version=sys.version_info[:3]; print("{0}".format(version[1]))' || { echo "no py3"; }` ["1"]=`python3 -c 'import sys; version=sys.version_info[:3]; print("{0}".format(version[2]))' || { echo "no py3"; }` )
PYTHON35_VERSION=`python3.7 -c 'import sys; version=sys.version_info[:3]; print("{0}".format(version[2]))' || { echo "no py37"; }`
PYTHON36_VERSION=`python3.8 -c 'import sys; version=sys.version_info[:3]; print("{0}".format(version[1]))' || { echo "no py38"; }`

if [ "$PYTHON37_VERSION" -eq "7" ]; then # Python3.7 = 3.7
    python3.7 run.py
    exit
fi

if [ "$PYTHON38_VERSION" -eq "8" ]; then # Python3.8 > 3.8
    python3.8 run.py
if

echo "You are running an unsupported Python version."
echo "Please use a version of Python above 3.7.0"
