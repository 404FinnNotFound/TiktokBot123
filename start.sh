#!/bin/bash

# Update package list
apt-get update

# Install FFmpeg without prompting
apt-get install -y ffmpeg

# Start the bot
python bot.py 