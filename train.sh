#!/bin/bash

# Check if both arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <folder> <config>"
    exit 1
fi

FOLDER=$1
CONFIG=$2

# Check if the folder exists
if [ ! -d "$FOLDER" ]; then
    echo "Error: Folder '$FOLDER' not found!"
    exit 1
fi

# Navigate to the folder
cd "$FOLDER" || exit 1

# Activate virtual environment
if [ ! -f "/workspace/SimpleTuner/.venv/bin/activate" ]; then
    echo "Error: Virtual environment not found in '$FOLDER'!"
    exit 1
fi

source /workspace/SimpleTuner/.venv/bin/activate

# Run the training script with the provided config
ENV=$CONFIG bash train.sh
