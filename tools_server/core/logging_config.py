import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def setup_logging():
    """Configure logging for the application"""
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create file handlers
    app_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS_DIR, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setFormatter(file_formatter)
    app_handler.setLevel(logging.INFO)
    
    auth_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS_DIR, 'auth.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    auth_handler.setFormatter(file_formatter)
    auth_handler.setLevel(logging.INFO)
    
    seller_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS_DIR, 'seller.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    seller_handler.setFormatter(file_formatter)
    seller_handler.setLevel(logging.INFO)
    
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS_DIR, 'errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setFormatter(file_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    auth_logger = logging.getLogger('auth')
    auth_logger.addHandler(auth_handler)
    
    seller_logger = logging.getLogger('seller')
    seller_logger.addHandler(seller_handler)
    
    return root_logger

def get_logger(name: str = None):
    """Get a logger instance"""
    if name:
        return logging.getLogger(name)
    return logging.getLogger()