#!/bin/bash

[ ! -d env ] && python3 -m venv env
source env/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# install dev dependencies
python -m pip install -r dev-requirements.txt
pre-commit install