#!/bin/bash

# Exit on error
set -e

# Create virtual environment if not already present
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip and install dependencies
echo "Upgrading pip and installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Environment setup complete."

#python3 -m scanner.engine.main
#python3 -m ai_transformer.engine.main