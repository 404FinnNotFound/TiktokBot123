# TikTok Video Bot

A Telegram bot that downloads and processes TikTok videos.

## Features

- Downloads TikTok videos in best quality using yt-dlp
- Crops videos to 5:7 aspect ratio
- Places videos on a 9:16 white background
- Adds user-provided captions using Chirp font
- Handles multiple requests efficiently
- Cleans up temporary files automatically

## Requirements

- Python 3.11+
- FFmpeg (required for video processing)
- Python packages listed in requirements.txt

## Local Development

1. Install FFmpeg:
   - On macOS: `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export BOT_TOKEN=your_telegram_bot_token
```

4. Run the bot:
```bash
python bot.py
```

## Deployment

This bot is configured for deployment on Railway.app. The following files are included:
- `Procfile` - Specifies the worker process
- `runtime.txt` - Specifies Python version
- `railway.toml` - Configures FFmpeg installation and other deployment settings

Make sure to set the `BOT_TOKEN` environment variable in your Railway project settings.

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