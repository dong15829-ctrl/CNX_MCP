#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Run the python script using the virtual environment
./venv/bin/python main.py >> morning_routine.log 2>&1
