# TikTok Video Processing Bot

A Telegram bot that downloads TikTok videos without watermarks and can add custom formatting with white borders and text overlays.

## Features

- Downloads TikTok videos without watermarks
- Option to add white borders (9:16 aspect ratio)
- Add custom text overlays with proper formatting
- Processes metadata to appear as original content
- Runs on Google Cloud for 24/7 availability

## Prerequisites

- Google Cloud account
- Telegram Bot Token (get it from [@BotFather](https://t.me/botfather))
- Basic knowledge of terminal commands

## Google Cloud Setup

1. Create a new VM instance:
   ```bash
   # Go to Google Cloud Console
   # Compute Engine > VM Instances > Create Instance
   Name: small-20250317-064004 (or any name you prefer)
   Region: us-central1
   Zone: us-central1-a
   Machine type: e2-micro (2 vCPU, 1 GB memory)
   Boot disk: Ubuntu 20.04 LTS (10GB)
   Allow HTTP/HTTPS traffic: Yes
   ```

2. Connect to your VM:
   ```bash
   gcloud compute ssh YOUR_INSTANCE_NAME --zone=us-central1-a
   ```

3. Install required system packages:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv ffmpeg fonts-liberation git
   ```

## Bot Setup

1. Clone the repository and set up environment:
   ```bash
   git clone https://github.com/YOUR_USERNAME/TiktokBot123.git
   cd TiktokBot123
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set up your bot token:
   ```bash
   echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env
   ```

3. Create systemd service for auto-start:
   ```bash
   sudo nano /etc/systemd/system/tiktok-bot.service
   ```
   
   Add this content (replace USER with your username):
   ```ini
   [Unit]
   Description=TikTok Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=USER
   WorkingDirectory=/home/USER/TiktokBot123
   Environment=PATH=/home/USER/TiktokBot123/venv/bin:$PATH
   EnvironmentFile=/home/USER/TiktokBot123/.env
   ExecStart=/home/USER/TiktokBot123/venv/bin/python bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. Start the bot service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tiktok-bot
   sudo systemctl start tiktok-bot
   ```

5. Check bot status:
   ```bash
   sudo systemctl status tiktok-bot
   ```

## Usage

1. Start a chat with your bot on Telegram
2. Send a TikTok video URL
3. Choose format:
   - "Download Only" - Gets video without watermark
   - "White Format" - Adds white borders and allows text overlay
4. If you chose "White Format", send your caption text (or "BLANK" to skip)

## Monitoring

View bot logs:
```bash
journalctl -u tiktok-bot -f
```

## Troubleshooting

If the bot stops working:
1. Check the logs:
   ```bash
   journalctl -u tiktok-bot -n 50
   ```

2. Restart the bot:
   ```bash
   sudo systemctl restart tiktok-bot
   ```

3. Common issues:
   - If font errors occur: `sudo apt-get install -y fonts-liberation`
   - If FFmpeg errors occur: `sudo apt-get install -y ffmpeg`
   - If permission errors: Check the service file user and paths

## License

MIT License - feel free to modify and distribute

## Contributing

Pull requests are welcome. For major changes, please open an issue first. 