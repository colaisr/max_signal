"""
Telegram bot service for publishing analysis results.
"""
from typing import Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Lazy import - only import if token is configured
_telegram_bot = None
_telegram_bot_token = None


def get_telegram_credentials(db: Optional[Session] = None) -> tuple[Optional[str], Optional[str]]:
    """Get Telegram bot token and channel ID from Settings (AppSettings table).
    
    Args:
        db: Database session (required)
    
    Returns:
        Tuple of (bot_token, channel_id) or (None, None) if not found
    """
    if not db:
        logger.error("Database session required to read Telegram credentials from Settings")
        return None, None
    
    try:
        from app.models.settings import AppSettings
        bot_token_setting = db.query(AppSettings).filter(
            AppSettings.key == "telegram_bot_token"
        ).first()
        channel_id_setting = db.query(AppSettings).filter(
            AppSettings.key == "telegram_channel_id"
        ).first()
        
        bot_token = bot_token_setting.value if bot_token_setting and bot_token_setting.value else None
        channel_id = channel_id_setting.value if channel_id_setting and channel_id_setting.value else None
        
        return bot_token, channel_id
    except Exception as e:
        logger.error(f"Failed to read Telegram credentials from Settings: {e}")
        return None, None


def get_telegram_bot(bot_token: Optional[str] = None):
    """Get or create Telegram bot instance.
    
    Args:
        bot_token: Optional bot token. If not provided, will use cached token.
    """
    global _telegram_bot, _telegram_bot_token
    
    if bot_token:
        _telegram_bot_token = bot_token
    
    if not _telegram_bot_token:
        logger.warning("Telegram bot token not configured")
        return None
    
    if _telegram_bot is None or _telegram_bot_token != bot_token:
        try:
            from telegram import Bot
            _telegram_bot = Bot(token=_telegram_bot_token)
        except ImportError:
            logger.error("python-telegram-bot not installed. Run: pip install python-telegram-bot")
            return None
    
    return _telegram_bot


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """Split message into chunks that fit Telegram's limit.
    
    Args:
        text: Message text to split
        max_length: Maximum length per chunk (default 4096 for Telegram)
    
    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Try to split by paragraphs first
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        # If adding this paragraph would exceed limit, save current chunk and start new
        if len(current_chunk) + len(para) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += '\n\n' + para
            else:
                current_chunk = para
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If still too long, split by lines
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            # Split by lines
            lines = chunk.split('\n')
            temp_chunk = ""
            for line in lines:
                if len(temp_chunk) + len(line) + 1 > max_length:
                    if temp_chunk:
                        final_chunks.append(temp_chunk.strip())
                    temp_chunk = line
                else:
                    if temp_chunk:
                        temp_chunk += '\n' + line
                    else:
                        temp_chunk = line
            if temp_chunk:
                final_chunks.append(temp_chunk.strip())
    
    return final_chunks


async def publish_to_telegram(message_text: str, db: Optional[Session] = None) -> dict:
    """Publish message to Telegram channel.
    
    Args:
        message_text: Text to publish
        db: Database session to read credentials from Settings
    
    Returns:
        Dict with 'success', 'message_ids', 'error'
    """
    # Get credentials from Settings
    bot_token, channel_id = get_telegram_credentials(db)
    
    if not bot_token:
        return {
            'success': False,
            'error': 'Telegram bot token not configured. Please set it in Settings → Telegram Configuration'
        }
    
    if not channel_id:
        return {
            'success': False,
            'error': 'Telegram channel ID not configured. Please set it in Settings → Telegram Configuration'
        }
    
    bot = get_telegram_bot(bot_token)
    if not bot:
        return {
            'success': False,
            'error': 'Failed to initialize Telegram bot'
        }
    
    try:
        # Split message if needed
        chunks = split_message(message_text)
        message_ids = []
        
        for i, chunk in enumerate(chunks):
            # Add part indicator if multiple chunks
            if len(chunks) > 1:
                chunk = f"📊 Часть {i + 1}/{len(chunks)}\n\n{chunk}"
            
            # Send message
            message = await bot.send_message(
                chat_id=channel_id,
                text=chunk,
                parse_mode=None  # Disable HTML parsing for now (can enable later if needed)
            )
            message_ids.append(message.message_id)
            
            logger.info(
                "telegram_message_sent",
                chunk=i + 1,
                total_chunks=len(chunks),
                message_id=message.message_id
            )
        
        return {
            'success': True,
            'message_ids': message_ids,
            'chunks_sent': len(chunks)
        }
    except Exception as e:
        logger.error("telegram_publish_failed", error=str(e))
        return {
            'success': False,
            'error': str(e)
        }

