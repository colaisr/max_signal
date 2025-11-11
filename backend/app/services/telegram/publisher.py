"""
Telegram bot service for publishing analysis results.
"""
from app.core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Lazy import - only import if token is configured
_telegram_bot = None


def get_telegram_bot():
    """Get or create Telegram bot instance."""
    global _telegram_bot
    
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured, Telegram publishing disabled")
        return None
    
    if _telegram_bot is None:
        try:
            from telegram import Bot
            _telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
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


async def publish_to_telegram(message_text: str) -> dict:
    """Publish message to Telegram channel.
    
    Args:
        message_text: Text to publish
    
    Returns:
        Dict with 'success', 'message_ids', 'error'
    """
    bot = get_telegram_bot()
    if not bot:
        return {
            'success': False,
            'error': 'Telegram bot not configured'
        }
    
    if not TELEGRAM_CHANNEL_ID:
        return {
            'success': False,
            'error': 'TELEGRAM_CHANNEL_ID not configured'
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
                chat_id=TELEGRAM_CHANNEL_ID,
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

