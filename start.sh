#!/bin/bash

echo "Checking FFmpeg installation..."

# Check FFmpeg
if command -v ffmpeg >/dev/null 2>&1; then
    echo "FFmpeg found at: $(which ffmpeg)"
    ffmpeg -version
else
    echo "ERROR: FFmpeg not found!"
    exit 1
fi

# Check FFprobe
if command -v ffprobe >/dev/null 2>&1; then
    echo "FFprobe found at: $(which ffprobe)"
    ffprobe -version
else
    echo "ERROR: FFprobe not found!"
    # Try to create symlink if ffprobe exists in alternative location
    if [ -f "/opt/ffmpeg/ffprobe" ]; then
        echo "Found ffprobe in /opt/ffmpeg, creating symlink..."
        ln -s /opt/ffmpeg/ffprobe /usr/local/bin/ffprobe
    elif [ -f "/usr/bin/ffprobe" ]; then
        echo "Found ffprobe in /usr/bin, creating symlink..."
        ln -s /usr/bin/ffprobe /usr/local/bin/ffprobe
    else
        echo "Could not find ffprobe in standard locations"
        exit 1
    fi
fi

echo "Starting Python bot..."
# Print Python version and path
python --version
which python

# Start the bot with error output
python bot.py 2>&1 