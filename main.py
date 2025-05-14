#!/usr/bin/env python3
"""
Music Indexer - An application for indexing and searching music collections.
"""
import sys
import os
import logging

from PyQt5.QtWidgets import QApplication
from music_indexer.gui.main_window import MainWindow
from music_indexer.utils.logger import get_logger


def setup_logging():
    """Set up application logging."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Get logger
    logger = get_logger("music_indexer", "INFO", True)
    
    return logger


def main():
    """Main entry point for the application."""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Music Indexer application")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Music Indexer")
    app.setOrganizationName("MusicIndexer")
    
    # Create a timer to ensure event processing
    from PyQt5.QtCore import QTimer
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Empty slot
    timer.start(100)  # Process events every 100ms
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Run application
    exit_code = app.exec_()
    
    logger.info(f"Application exited with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
