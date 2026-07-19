#!/bin/sh
set -e

# Change to the directory where this script is located
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "Initializing NutriCloud Agent..."

# Ensure we have a virtual environment
if [ ! -d ".venv" ]; then
    echo "-> Creating Python virtual environment..."
    # --system-site-packages allows the venv to see the pre-compiled py3-cryptography we install via apk
    python3 -m venv --system-site-packages .venv
fi

echo "-> Activating virtual environment..."
. .venv/bin/activate

echo "-> Installing missing dependencies..."
pip install --upgrade pip
pip install -r nutricloud_manager/requirements.txt

echo "-> Starting the agent..."
cd nutricloud_manager
python3 agent.py
