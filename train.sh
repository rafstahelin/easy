#!/bin/bash

# Fail on errors
set -e

# Check if both arguments are provided - used by Easy tool
if [ $# -eq 2 ]; then
    SIMPLETUNER_PATH="$1"
    CONFIG="$2"
    
    # Navigate to SimpleTuner directory
    cd "$SIMPLETUNER_PATH" || {
        echo "Error: Cannot navigate to $SIMPLETUNER_PATH"
        exit 1
    }
    
    # Activate virtual environment
    if [ ! -f ".venv/bin/activate" ]; then
        echo "Error: Virtual environment not found in '$SIMPLETUNER_PATH'!"
        exit 1
    fi
    
    source .venv/bin/activate
    
    # Run the training script with the provided config
    ENV="$CONFIG" bash train.sh
    exit 0
fi

# Direct invocation with partial config name
if [ $# -eq 1 ]; then
    # Function to find a config directory that matches the partial name
    find_config() {
        local partial_name="$1"
        local config_dir="/workspace/SimpleTuner/config"
        
        # Check if config directory exists
        if [ ! -d "$config_dir" ]; then
            echo "Error: Config directory not found at $config_dir"
            return 1
        fi
        
        # Search for configs matching the partial name
        matching_configs=$(find "$config_dir" -maxdepth 1 -type d -name "*${partial_name}*" | sort)
        matching_count=$(echo "$matching_configs" | grep -v "^$" | wc -l)
        
        if [ "$matching_count" -eq 0 ]; then
            echo "Error: No configs found matching '$partial_name'"
            return 1
        elif [ "$matching_count" -gt 1 ]; then
            echo "Found multiple matching configs:"
            echo "$matching_configs" | sed 's|.*/||' | nl
            echo "Please specify a more precise name."
            return 1
        else
            # Extract just the directory name without the path
            config_name=$(echo "$matching_configs" | sed 's|.*/||')
            echo "$config_name"
            return 0
        fi
    }

    # Find the full config name based on partial match
    PARTIAL_CONFIG="$1"
    FULL_CONFIG=$(find_config "$PARTIAL_CONFIG")

    if [ $? -ne 0 ]; then
        # Error message already shown by find_config
        exit 1
    fi

    echo "Found matching config: $FULL_CONFIG"

    # Navigate to SimpleTuner directory
    cd /workspace/SimpleTuner || {
        echo "Error: Cannot navigate to /workspace/SimpleTuner"
        exit 1
    }

    # Activate the virtual environment
    if [ ! -d ".venv" ]; then
        echo "Error: Virtual environment not found at /workspace/SimpleTuner/.venv"
        exit 1
    fi

    source .venv/bin/activate

    # Set environment variables
    export DISABLE_UPDATES=1

    # Run the training command
    echo "Starting training with config: $FULL_CONFIG"
    ENV="$FULL_CONFIG" bash train.sh
    exit 0
fi

# If we got here, no valid arguments were provided
echo "Usage: $(basename "$0") <partial-config-name>"
echo "   OR: $(basename "$0") <simpletuner-path> <full-config-name> (for use by Easy tool)"
exit 1