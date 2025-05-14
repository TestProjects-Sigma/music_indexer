"""
Logger module for the music indexer application.
Provides customized logging functionality.
"""
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


class Logger:
    """Custom logger for the music indexer application."""
    
    def __init__(self, name="music_indexer", log_level="INFO", log_to_console=True):
        """Initialize logger with specified name and level. Log_level can be INFO or DEBUG"""
        self.logger = logging.getLogger(name)
        
        # Set log level
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Clear any existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # Create file handler
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(
            log_dir, 
            f"music_indexer_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message):
        """Log critical message."""
        self.logger.critical(message)


# Singleton instance
_logger_instance = None


def get_logger(name="music_indexer", log_level=None, log_to_console=True):
    """Get or create the logger instance."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = Logger(name, log_level or "DEBUG", log_to_console)
    
    return _logger_instance
