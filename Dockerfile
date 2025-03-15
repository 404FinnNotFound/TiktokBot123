FROM python:3.11-slim

# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libavfilter-dev \
    x264 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify FFmpeg installation and create symlinks if needed
RUN ffmpeg -version && \
    ffprobe -version && \
    ln -sf $(which ffmpeg) /usr/local/bin/ffmpeg && \
    ln -sf $(which ffprobe) /usr/local/bin/ffprobe

# Set working directory
WORKDIR /app

# Create directory for temporary files with proper permissions
RUN mkdir -p /tmp/video_processing && \
    chmod 777 /tmp/video_processing && \
    chown nobody:nogroup /tmp/video_processing

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variable for temporary directory
ENV TEMP_DIR=/tmp/video_processing

# Switch to non-root user for security
USER nobody

# Run the bot
CMD ["python", "bot.py"] 