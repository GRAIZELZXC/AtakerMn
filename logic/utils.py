#!/usr/bin/env python3

"""
Utility functions for Bittensor registration assistant
"""

import logging
import requests
import time
from bittensor_registration.config import TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def setup_logging():
    """Setup logger for the application"""
    # Setup logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("registration.log")
        ]
    )
    logger = logging.getLogger("registration")
    
    # Setup colorama if available
    try:
        import colorama
        from colorama import Fore, Style
        colorama.init(autoreset=True)
    except:
        # Create simple ASCII replacements if colorama fails
        class SimpleColors:
            def __init__(self):
                self.GREEN = ''
                self.RED = ''
                self.YELLOW = ''
                self.CYAN = ''
                self.RESET_ALL = ''
    
    return logger

def send_telegram(message):
    """Send notification via Telegram"""
    logger = logging.getLogger("registration")
    
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
        
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.debug("Telegram notification sent")
            return True
        else:
            logger.error(f"Telegram notification failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        return False

def safe_input(prompt, default=None):
    """Get input safely with default value"""
    try:
        user_input = input(prompt).strip()
        return user_input if user_input else default
    except:
        return default