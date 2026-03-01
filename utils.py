"""
Utility functions for IICCC system
"""

import logging
from datetime import datetime
import os

def setup_logging():
    """Configure logging for the entire system"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create logger
    logger = logging.getLogger('IICCC')
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate logs if called multiple times
    if logger.handlers:
        return logger
    
    # File handler (saves to file)
    log_filename = f"logs/iiccc_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Console handler (prints to terminal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
