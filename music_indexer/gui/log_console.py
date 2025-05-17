"""
Log console widget for the music indexer application.
"""
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
import logging

from ..utils.logger import get_logger
logger = get_logger()

# Create custom logging handler for Qt
class QTextEditLogger(QObject, logging.Handler):
    """Custom logging handler that outputs to a QTextEdit."""
    
    # Signal to emit when new log record is available
    log_record = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        """Initialize the handler."""
        super().__init__(parent)
        self.setLevel(logging.INFO)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                          datefmt='%H:%M:%S'))
        self.widget = None
    
    def connect_widget(self, widget):
        """Connect to a QTextEdit widget."""
        self.widget = widget
        self.log_record.connect(widget.append_log)
    
    def emit(self, record):
        """Emit a log record."""
        try:
            msg = self.format(record)
            self.log_record.emit(msg, record.levelno)
        except Exception:
            self.handleError(record)


class LogConsole(QWidget):
    """Widget for displaying log messages in the application."""
    
    def __init__(self, parent=None):
        """Initialize the log console."""
        super().__init__(parent)
        
        # Store parent reference
        self.parent_widget = parent
        
        # Create handler with parent
        self.log_handler = QTextEditLogger(self)
        self.setup_ui()
        self.setup_logging()

    
    def setup_ui(self):
        """Set up the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create header layout
        header_layout = QHBoxLayout()
        
        # Add title
        title_label = QLabel("Application Log")
        title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(title_label)
        
        # Add spacer
        header_layout.addStretch()
        
        # Add level filter checkboxes
        self.debug_check = QCheckBox("Debug")
        self.debug_check.setChecked(False)
        self.debug_check.toggled.connect(self.update_log_level)
        
        self.info_check = QCheckBox("Info")
        self.info_check.setChecked(True)
        self.info_check.toggled.connect(self.update_log_level)
        
        self.warning_check = QCheckBox("Warning")
        self.warning_check.setChecked(True)
        self.warning_check.toggled.connect(self.update_log_level)
        
        self.error_check = QCheckBox("Error")
        self.error_check.setChecked(True)
        self.error_check.toggled.connect(self.update_log_level)
        
        header_layout.addWidget(self.debug_check)
        header_layout.addWidget(self.info_check)
        header_layout.addWidget(self.warning_check)
        header_layout.addWidget(self.error_check)
        
        # Add clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_log)
        header_layout.addWidget(self.clear_button)
        
        # Add header to main layout
        main_layout.addLayout(header_layout)
        
        # Create log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        font = QFont("Consolas, Courier New, monospace")
        font.setPointSize(9)
        self.log_text.setFont(font)
        
        # Set up text formats for different log levels
        self.text_formats = {
            logging.DEBUG: self.create_format(QColor(100, 100, 100)),  # Gray
            logging.INFO: self.create_format(QColor(0, 0, 0)),          # Black
            logging.WARNING: self.create_format(QColor(255, 140, 0)),   # Orange
            logging.ERROR: self.create_format(QColor(200, 0, 0)),        # Red
            logging.CRITICAL: self.create_format(QColor(150, 0, 0))      # Dark Red
        }
        
        # Connect the log handler to this widget
        self.log_handler.connect_widget(self)
        
        # Add log text to main layout
        main_layout.addWidget(self.log_text)
    
    def create_format(self, color):
        """Create a text format with specified color."""
        text_format = QTextCharFormat()
        text_format.setForeground(color)
        return text_format
    
    def setup_logging(self):
        """Set up logging integration."""
        # Get the root logger
        root_logger = logging.getLogger()
        
        # Add our handler to the root logger if not already added
        if self.log_handler not in root_logger.handlers:
            root_logger.addHandler(self.log_handler)
        
        # Set initial log level
        self.update_log_level()

    def removeHandler(self):
        """Remove our handler from the logging system."""
        if hasattr(self, 'log_handler'):
            root_logger = logging.getLogger()
            if self.log_handler in root_logger.handlers:
                root_logger.removeHandler(self.log_handler)
                self.log_handler = None

    def destroy(self, destroyWindow=True, destroySubWindows=True):
        """Override to clean up logging handler."""
        self.removeHandler()
        super().destroy(destroyWindow, destroySubWindows)

    @pyqtSlot(str, int)
    def append_log(self, message, level):
        """Append a log message with proper formatting."""
        # Check if this log level should be displayed
        if ((level == logging.DEBUG and not self.debug_check.isChecked()) or
            (level == logging.INFO and not self.info_check.isChecked()) or
            (level == logging.WARNING and not self.warning_check.isChecked()) or
            (level == logging.ERROR and not self.error_check.isChecked() and 
             level != logging.CRITICAL)):
            return
        
        # Get text cursor and format for this level
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Apply formatting
        format_to_use = self.text_formats.get(level, self.text_formats[logging.INFO])
        cursor.setCharFormat(format_to_use)
        
        # Insert text
        cursor.insertText(message + "\n")
        
        # Scroll to bottom
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
    
    def update_log_level(self):
        """Update the log level based on checkbox states."""
        # Set the handler level to the minimum enabled level
        if self.debug_check.isChecked():
            self.log_handler.setLevel(logging.DEBUG)
        elif self.info_check.isChecked():
            self.log_handler.setLevel(logging.INFO)
        elif self.warning_check.isChecked():
            self.log_handler.setLevel(logging.WARNING)
        elif self.error_check.isChecked():
            self.log_handler.setLevel(logging.ERROR)
        else:
            self.log_handler.setLevel(logging.CRITICAL)
    
    def clear_log(self):
        """Clear the log text area."""
        self.log_text.clear()
    
    def log_message(self, message, level=logging.INFO):
        """Manually log a message."""
        logger = logging.getLogger()
        logger.log(level, message)

    def cleanup(self):
        """Clean up before deletion."""
        self.removeHandler()
        try:
            if hasattr(self, 'log_handler') and hasattr(self.log_handler, 'log_record'):
                self.log_handler.log_record.disconnect()
        except:
            pass