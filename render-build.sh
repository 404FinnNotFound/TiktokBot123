#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies
sudo apt-get update
sudo apt-get install -y ffmpeg

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
