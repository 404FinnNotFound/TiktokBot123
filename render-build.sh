#!/bin/bash
set -eux

# Install FFmpeg in the Render environment
curl -fsSL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ
mkdir -p $HOME/bin
mv ffmpeg-*-static/ffmpeg $HOME/bin/
mv ffmpeg-*-static/ffprobe $HOME/bin/
export PATH="$HOME/bin:$PATH"
