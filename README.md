# TikTok Video Processing Telegram Bot

A Telegram bot that downloads TikTok videos without watermarks, adds custom captions, and processes them for optimal viewing.

## Features

- Downloads TikTok videos without watermarks
- Adds custom text captions to videos
- Processes videos to optimal dimensions
- Maintains authentic video metadata
- Handles long captions with automatic line breaks

## Deployment on Railway

1. Fork this repository to your GitHub account
2. Create a new project on [Railway](https://railway.app/)
3. Connect your GitHub repository to Railway
4. Add the following environment variable in Railway:
   - `BOT_TOKEN`: Your Telegram bot token from [@BotFather](https://t.me/BotFather)

The bot will automatically deploy and start running on Railway.

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-bot.git
cd telegram-bot
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your bot token:
```
BOT_TOKEN=your_bot_token_here
```

4. Run the bot:
```bash
python bot.py
```

## Usage

1. Start a chat with your bot on Telegram
2. Send a TikTok video URL to the bot
3. Add an optional caption text
4. The bot will process and return the video with your caption

## Requirements

- Python 3.11.7
- FFmpeg
- Dependencies listed in requirements.txt

## License

MIT License 