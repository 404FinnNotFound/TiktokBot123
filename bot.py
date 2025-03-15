import os
import logging
from typing import Optional, Dict
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import tempfile
import re
import signal
import atexit
import subprocess
import json
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7538731330:AAFSOY0g0vSaEGaFV1zat2Ll-6Aeh_dv49o"

# Lock file path
LOCK_FILE = "bot.lock"

# Get temp directory from environment variable or use system temp
TEMP_DIR = os.getenv('TEMP_DIR', tempfile.gettempdir())
os.makedirs(TEMP_DIR, exist_ok=True)
logger.info(f"Using temporary directory: {TEMP_DIR}")

# Video aspect ratio settings
VIDEO_RATIO_WIDTH = 5    # Target video aspect ratio width
VIDEO_RATIO_HEIGHT = 7   # Target video aspect ratio height
BG_RATIO_WIDTH = 9      # Background aspect ratio width
BG_RATIO_HEIGHT = 16    # Background aspect ratio height

# Border padding settings
SIDE_PADDING_PERCENT = 6  # How much white space to add on each side
TOP_PADDING_PERCENT = 25   # How much white space to add on top (reduced from 25 to push video up)
BOTTOM_PADDING_PERCENT = 5  # How much white space to add on bottom

# Final output resolution (adjust for quality vs file size)
FINAL_HEIGHT = 1920  # Final height in pixels (16:9 ratio will make width 1080)
FINAL_WIDTH = int(FINAL_HEIGHT * BG_RATIO_WIDTH / BG_RATIO_HEIGHT)  # Calculate width based on 9:16 ratio

# Conversation states
CHOOSING_FORMAT = 1
WAITING_FOR_CAPTION = 2

# Callback data
DOWNLOAD_ONLY = "download_only"
META_FORMAT = "meta_format"

# Store temporary video paths
temp_videos: Dict[int, str] = {}

def cleanup():
    """Clean up function to remove lock file on exit."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception as e:
        logger.error(f"Error cleaning up lock file: {e}")

def signal_handler(signum, frame):
    """Handle termination signals."""
    cleanup()
    exit(0)

# Register cleanup functions
atexit.register(cleanup)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! Send me a TikTok URL and I'll send you back the video without the watermark."
    )

def crop_video(input_path: str) -> str:
    """Crop video to target aspect ratio using FFmpeg."""
    output_path = os.path.join(TEMP_DIR, "cropped_video.mp4")
    
    try:
        # Get video dimensions using ffprobe
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            input_path
        ]
        
        probe_output = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        video_info = json.loads(probe_output.stdout)
        
        # Extract current dimensions
        current_width = int(video_info['streams'][0]['width'])
        current_height = int(video_info['streams'][0]['height'])
        
        # Calculate target dimensions to maintain aspect ratio
        current_ratio = current_width / current_height
        target_ratio = VIDEO_RATIO_WIDTH / VIDEO_RATIO_HEIGHT
        
        if current_ratio > target_ratio:
            # Video is too wide, crop width
            new_width = int(current_height * target_ratio)
            new_height = current_height
            x_offset = (current_width - new_width) // 2
            y_offset = 0
        else:
            # Video is too tall, crop height
            new_width = current_width
            new_height = int(current_width / target_ratio)
            x_offset = 0
            y_offset = (current_height - new_height) // 2
        
        # Construct FFmpeg command with crop
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f'crop={new_width}:{new_height}:{x_offset}:{y_offset}',
            '-c:a', 'copy',  # Copy audio stream without re-encoding
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        # Run FFmpeg
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Remove original file
        os.remove(input_path)
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        raise Exception("Failed to crop video")
    except Exception as e:
        logger.error(f"Error cropping video: {e}")
        raise

def add_border(input_path: str) -> str:
    """Add white borders to make video 9:16 while maintaining 5:7 content ratio."""
    output_path = os.path.join(TEMP_DIR, "bordered_video.mp4")
    
    try:
        # Get video dimensions using ffprobe
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            input_path
        ]
        
        probe_output = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        video_info = json.loads(probe_output.stdout)
        input_width = int(video_info['streams'][0]['width'])
        input_height = int(video_info['streams'][0]['height'])
        logger.info(f"Input video dimensions: {input_width}x{input_height}")
        
        # Calculate final dimensions (9:16)
        final_height = FINAL_HEIGHT
        final_width = int(final_height * BG_RATIO_WIDTH / BG_RATIO_HEIGHT)
        logger.info(f"Target dimensions: {final_width}x{final_height}")
        logger.info(f"Using padding settings - Side: {SIDE_PADDING_PERCENT}%, Top: {TOP_PADDING_PERCENT}%, Bottom: {BOTTOM_PADDING_PERCENT}%")
        
        # Calculate available space after padding
        side_padding = int(final_width * SIDE_PADDING_PERCENT / 100)
        top_padding = int(final_height * TOP_PADDING_PERCENT / 100)
        bottom_padding = int(final_height * BOTTOM_PADDING_PERCENT / 100)
        
        # Calculate maximum video dimensions that will fit with padding
        max_video_width = final_width - (2 * side_padding)
        max_video_height = final_height - (top_padding + bottom_padding)
        
        logger.info(f"Available space for video: {max_video_width}x{max_video_height}")
        
        # Calculate video dimensions to fit in available space while maintaining 5:7 ratio
        target_ratio = VIDEO_RATIO_WIDTH / VIDEO_RATIO_HEIGHT
        current_ratio = max_video_width / max_video_height
        
        if current_ratio > target_ratio:
            # Height is the limiting factor
            video_height = max_video_height
            video_width = int(video_height * target_ratio)
            # Recalculate side padding to maintain percentage
            side_padding = int(final_width * SIDE_PADDING_PERCENT / 100)
        else:
            # Width is the limiting factor
            video_width = max_video_width
            video_height = int(video_width / target_ratio)
            # Keep original top and bottom padding
        
        logger.info(f"Final video dimensions: {video_width}x{video_height}")
        logger.info(f"Padding - Side: {side_padding}px, Top: {top_padding}px, Bottom: {bottom_padding}px")
        
        # Construct FFmpeg command
        filter_complex = [
            f'scale={video_width}:{video_height}',  # Scale video
            f'pad={final_width}:{final_height}:{side_padding}:{top_padding}:color=white'  # Add padding
        ]
        
        logger.info(f"Final FFmpeg filter: {','.join(filter_complex)}")
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', ','.join(filter_complex),
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        # Run FFmpeg
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Remove original file
        os.remove(input_path)
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        raise Exception("Failed to add borders to video")
    except Exception as e:
        logger.error(f"Error adding borders: {e}")
        raise

def check_metadata(file_path: str) -> dict:
    """Check video metadata using FFprobe."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Error checking metadata: {e}")
        return {}

def modify_metadata(input_path: str, metadata: dict) -> str:
    """Modify video metadata using FFmpeg."""
    output_path = os.path.join(TEMP_DIR, "metadata_video.mp4")
    
    try:
        # Prepare metadata arguments
        metadata_args = []
        for key, value in metadata.items():
            metadata_args.extend(['-metadata', f'{key}={value}'])
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c', 'copy'
        ] + metadata_args + [
            '-y',
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Remove original file
        os.remove(input_path)
        
        return output_path
    except Exception as e:
        logger.error(f"Error modifying metadata: {e}")
        raise

def generate_authentic_metadata() -> dict:
    """Generate authentic-looking metadata for a mobile-recorded video."""
    # List of common mobile devices
    mobile_devices = [
        "iPhone 15",
        "iPhone 14 Pro",
        "iPhone 14",
        "iPhone 13 Pro",
        "Samsung Galaxy S23",
        "Google Pixel 8",
        "Samsung Galaxy S24"
    ]
    
    # Mobile video encoders
    encoders = [
        "H.264/AVC", "HEVC/H.265", "VideoToolbox"
    ]
    
    # Generate a random recent timestamp (within last 24 hours for freshness)
    random_hours = random.uniform(0.5, 24)
    creation_time = datetime.now() - timedelta(hours=random_hours)
    
    # Generate random but realistic mobile bitrates (2-4 Mbps for mobile video)
    video_bitrate = random.randint(2000, 4000)
    audio_bitrate = random.choice([96, 128, 192])
    
    return {
        # Technical metadata
        'encoder': random.choice(encoders),
        'creation_tool': f"Mobile Camera ({random.choice(mobile_devices)})",
        'encoded_date': creation_time.strftime('%Y-%m-%d %H:%M:%S'),
        'tagged_date': creation_time.strftime('%Y-%m-%d %H:%M:%S'),
        'encoding-settings': f'baseline / bitrate={video_bitrate}k',
        'handler_name': 'Camera Media',
        'vendor_id': 'Apple',
        
        # Content metadata
        'major_brand': 'mp42',
        'minor_version': '1',
        'compatible_brands': 'mp42isom',
        'date': creation_time.strftime('%Y-%m-%d'),
        'creation_time': creation_time.strftime('%Y-%m-%d %H:%M:%S'),
        
        # Audio metadata
        'audio_bitrate': f'{audio_bitrate}k',
        'audio_format': 'AAC LC',
        'channel_layout': 'stereo',
        
        # Remove any metadata that might identify it as a processed video
        'comment': '',
        'description': '',
        'title': '',
        'artist': '',
        'copyright': ''
    }

def process_video_metadata(video_path: str, info: dict) -> str:
    """Process and modify video metadata to appear as a fresh video."""
    try:
        # Check if metadata can be modified
        current_metadata = check_metadata(video_path)
        if not current_metadata:
            logger.warning("Could not read current metadata")
            return video_path
        
        # Generate authentic-looking metadata
        new_metadata = generate_authentic_metadata()
        
        # Modify metadata
        processed_path = modify_metadata(video_path, new_metadata)
        
        # Verify changes
        updated_metadata = check_metadata(processed_path)
        if not updated_metadata:
            logger.warning("Could not verify metadata changes")
            return processed_path
        
        logger.info("Metadata successfully updated with authentic values")
        return processed_path
        
    except Exception as e:
        logger.error(f"Error processing metadata: {e}")
        return video_path

def download_tiktok_no_border(url: str) -> str:
    """Download TikTok video without adding borders."""
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'file_access_retries': 5,
            'extractor_args': {
                'TikTok': {
                    'download_without_watermark': True,
                    'no_watermark': True,
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract video info and download
                info = ydl.extract_info(url, download=True)
                video_path = os.path.join(TEMP_DIR, f"video.mp4")
                
                # Process metadata
                return process_video_metadata(video_path, info)
                
            except Exception as e:
                logger.error(f"Download error: {str(e)}")
                raise Exception(f"Failed to download video (try again): {str(e)}")
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise Exception("Failed to download video")

def download_tiktok(url: str) -> str:
    """Download and process TikTok video."""
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'file_access_retries': 5,
            'extractor_args': {
                'TikTok': {
                    'download_without_watermark': True,
                    'no_watermark': True,
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract video info and download
                info = ydl.extract_info(url, download=True)
                downloaded_path = os.path.join(TEMP_DIR, f"video.mp4")
                
                # Process metadata
                processed_path = process_video_metadata(downloaded_path, info)
                
                # First crop to 5:7 ratio
                cropped_path = crop_video(processed_path)
                
                # Then add white borders to make it 9:16
                return add_border(cropped_path)
                
            except Exception as e:
                logger.error(f"Download error: {str(e)}")
                raise Exception(f"Failed to download video (try again): {str(e)}")
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise Exception("Failed to download video")

def add_text_overlay(input_path: str, text: str) -> str:
    """Add text overlay to video."""
    output_path = os.path.join(TEMP_DIR, "text_overlay.mp4")
    
    try:
        # Position text at a fixed distance from the top of the frame
        y_position = 396  # Default position for multi-line text
        
        # Add line breaks every 56 characters
        formatted_text = ""
        remaining_text = text
        while len(remaining_text) > 50:
            # Find the last space before 56 characters to break at word boundaries
            break_point = remaining_text[:50].rstrip().rfind(' ')
            if break_point == -1:  # No space found, force break at 56
                break_point = 50
            formatted_text += remaining_text[:break_point] + '\n'
            remaining_text = remaining_text[break_point:].lstrip()
        formatted_text += remaining_text
        
        # Count number of lines
        num_lines = formatted_text.count('\n') + 1
        
        # Adjust position based on number of lines
        if num_lines == 1 and len(text) <= 50:
            # For single short line, position text higher
            y_position = 396  # Move text up significantly for single line
        else:
            # For multiple lines, move up by 50 pixels per additional line
            y_position = y_position - (50 * (num_lines - 1))
        
        # Calculate x position for left alignment (with small margin)
        side_padding = int(FINAL_WIDTH * SIDE_PADDING_PERCENT / 100)  # Get the actual side padding
        x_position = side_padding + 13  # Position text 25 pixels from where video starts
        
        # Escape special characters in text
        escaped_text = formatted_text.replace("'", "'\\\\\\''").replace(':', '\\:').replace('=', '\\=')
        
        # Construct FFmpeg command with text overlay
        filter_complex = f"drawtext=text='{escaped_text}':fontfile=/System/Library/Fonts/HelveticaNeue.ttc:fontsize=45:fontcolor=#0F1419:line_spacing=8:x={x_position}:y={y_position}:box=0"
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', filter_complex,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        # Run FFmpeg with error output capture
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Remove original file
        os.remove(input_path)
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        raise Exception(f"Failed to add text overlay: {e.stderr}")
    except Exception as e:
        logger.error(f"Error adding text overlay: {e}")
        raise

async def handle_video_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the initial TikTok URL and show format options."""
    try:
        url = update.message.text.strip()
        
        # Validate TikTok URL
        if not re.match(r'https?://(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)/', url):
            await update.message.reply_text("Please provide a valid TikTok URL.")
            return ConversationHandler.END
        
        # Store URL in context
        context.user_data['tiktok_url'] = url
        
        # Create inline keyboard with format options
        keyboard = [
            [
                InlineKeyboardButton("Download Only", callback_data=DOWNLOAD_ONLY),
                InlineKeyboardButton("White Format", callback_data=META_FORMAT)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send options message
        message = await update.message.reply_text(
            "Choose your format:\n\n"
            "📥 Download Only - Just the video without watermark\n"
            "✨ White Format - White background + caption text",
            reply_markup=reply_markup
        )
        context.user_data['options_message'] = message
        
        return CHOOSING_FORMAT
            
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
        return ConversationHandler.END

async def handle_format_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's format choice."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Get the stored URL
        url = context.user_data.get('tiktok_url')
        if not url:
            await query.message.edit_text("Sorry, something went wrong. Please send the TikTok URL again.")
            return ConversationHandler.END
        
        # Update message to show processing
        await query.message.edit_text("⏳ Starting download...", reply_markup=None)
        context.user_data['status_message'] = query.message
        
        if query.data == DOWNLOAD_ONLY:
            # Process video without borders
            try:
                video_path = download_tiktok_no_border(url)
                temp_videos[update.effective_user.id] = video_path
                
                # Send video directly
                await send_final_video(update, context, video_path)
                return ConversationHandler.END
                
            except Exception as e:
                await handle_download_error(query.message, e)
                return ConversationHandler.END
        
        elif query.data == META_FORMAT:
            # Process video with borders
            try:
                video_path = download_tiktok(url)
                temp_videos[update.effective_user.id] = video_path
                
                # Ask for caption
                await query.message.edit_text(
                    "Video processed! Please send the caption text you want to add to the top of the video.\n\n"
                    "Or send 'BLANK' to skip adding text."
                )
                return WAITING_FOR_CAPTION
                
            except Exception as e:
                await handle_download_error(query.message, e)
                return ConversationHandler.END
    
    except Exception as e:
        await query.message.edit_text(f"An error occurred: {str(e)}")
        return ConversationHandler.END

async def handle_download_error(message: "Message", error: Exception):
    """Handle download errors with appropriate messages."""
    error_msg = str(error).lower()
    if "timed out" in error_msg:
        await message.edit_text("Download timed out. Please try again or try a different video.")
    elif "too large" in error_msg:
        await message.edit_text("Video is too large for Telegram (max 50MB). Try a shorter video.")
    else:
        await message.edit_text(f"Error processing video: {str(error)}")

async def send_final_video(update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: str):
    """Send the final video and clean up."""
    try:
        status_message = context.user_data.get('status_message')
        
        # Check file size
        file_size = os.path.getsize(video_path)
        if file_size > 50 * 1024 * 1024:
            await status_message.edit_text("⚠️ Video is too large for Telegram (max 50MB). Try a shorter video.")
            return
        
        await status_message.edit_text("📤 Uploading to Telegram...")
        
        # Send the video
        if update.callback_query:
            message = update.callback_query.message
        else:
            message = update.message
            
        with open(video_path, 'rb') as video_file:
            await message.reply_video(
                video_file,
                caption="Here's your video! 🎬",
                supports_streaming=True,
                read_timeout=60,
                write_timeout=60,
                connect_timeout=60,
                pool_timeout=60,
            )
        
        # Clean up
        try:
            os.remove(video_path)
            os.rmdir(os.path.dirname(video_path))
            del temp_videos[update.effective_user.id]
        except Exception as e:
            logger.warning(f"Error cleaning up files: {str(e)}")
        
        await status_message.delete()
        
    except Exception as e:
        if status_message:
            await status_message.edit_text(f"Error sending video: {str(e)}")

async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the caption text and finalize the video."""
    try:
        caption_text = update.message.text.strip()
        status_message = context.user_data.get('status_message')
        video_path = temp_videos.get(update.effective_user.id)
        
        if not video_path:
            await update.message.reply_text("Sorry, I can't find your video. Please try sending the TikTok URL again.")
            return ConversationHandler.END
        
        try:
            if caption_text.upper() != "BLANK":
                # Add text overlay
                video_path = add_text_overlay(video_path, caption_text)
            
            # Check file size
            file_size = os.path.getsize(video_path)
            if file_size > 50 * 1024 * 1024:
                await status_message.edit_text("⚠️ Video is too large for Telegram (max 50MB). Try a shorter video.")
                return ConversationHandler.END
            
            await status_message.edit_text("📤 Uploading to Telegram...")
            
            # Send the video
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(
                    video_file,
                    caption="Here's your video! 🎬",
                    supports_streaming=True,
                    read_timeout=60,
                    write_timeout=60,
                    connect_timeout=60,
                    pool_timeout=60,
                )
            
            # Clean up
            try:
                os.remove(video_path)
                os.rmdir(os.path.dirname(video_path))
                del temp_videos[update.effective_user.id]
            except Exception as e:
                logger.warning(f"Error cleaning up files: {str(e)}")
            
            await status_message.delete()
            
        except Exception as e:
            await update.message.reply_text(f"Error processing video: {str(e)}")
            
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
    
    return ConversationHandler.END

def main():
    """Start the bot."""
    try:
        # Check for existing lock file
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        
        # Create lock file
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        # Create application
        application = (
            Application.builder()
            .token(TOKEN)
            .get_updates_read_timeout(60)
            .get_updates_write_timeout(60)
            .connection_pool_size(8)
            .pool_timeout(30.0)
            .build()
        )
        
        # Create conversation handler
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r'https?://(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)/'), handle_video_url)],
            states={
                CHOOSING_FORMAT: [CallbackQueryHandler(handle_format_choice)],
                WAITING_FOR_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_caption)],
            },
            fallbacks=[],
        )
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(conv_handler)
        application.add_error_handler(error_handler)
        
        # Start the Bot
        print("Starting bot...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            pool_timeout=None,
            read_timeout=60,
            write_timeout=60,
        )
        
    except Exception as e:
        print(f"Error starting bot: {e}")
        cleanup()
    finally:
        cleanup()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram-python-bot library."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Get the error message
    error_msg = str(context.error)
    
    if "Conflict:" in error_msg:
        # Bot instance conflict
        logger.error("Another bot instance is already running!")
        return
    
    # Send error message to user
    if update and update.effective_message:
        error_text = "Sorry, an error occurred while processing your request."
        await update.effective_message.reply_text(error_text)

if __name__ == '__main__':
    main() 