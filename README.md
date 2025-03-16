# TikTok Video Processing Telegram Bot

This bot downloads TikTok videos, processes them to a specific format, adds captions, and sends them back to users via Telegram.

## Features

- Downloads TikTok videos in best quality using yt-dlp
- Crops videos to 5:7 aspect ratio
- Places videos on a 9:16 white background
- Adds user-provided captions using Chirp font
- Handles multiple requests efficiently
- Cleans up temporary files automatically

## Requirements

- Python 3.8 or higher
- FFmpeg installed on your system
- Chirp font installed on your system

## Installation

1. Install FFmpeg:
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt-get install ffmpeg`
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

2. Install the Chirp font:
   - Download from [Chirp font website](https://chirp.twitter.com/)
   - Install it on your system

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the bot:
   ```bash
   python bot.py
   ```

2. In Telegram, send a message to the bot in the following format:
   ```
   <TikTok URL> | Your caption here
   ```

   Example:
   ```
   https://www.tiktok.com/@user/video/1234567890 | This is my caption
   ```

3. The bot will process the video and send it back to you.

## Error Handling

The bot includes error handling for:
- Invalid TikTok URLs
- Failed downloads
- Processing errors
- Invalid message formats

## Notes

- Videos are processed with a 5:7 aspect ratio and placed on a 9:16 white background
- Captions are added above the video in black Chirp font
- All temporary files are automatically cleaned up after processing 