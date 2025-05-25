"""
Main window GUI for the music indexer application.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStatusBar, QMessageBox,
    QFileDialog, QProgressDialog, QAction, QMenu, QCheckBox
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon

from ..utils.logger import get_logger
logger = get_logger()
from ..utils.config_manager import ConfigManager
from .. import MusicIndexer

# Import GUI panels
from .search_panel import SearchPanel
from .results_panel import EnhancedResultsPanel
from .settings_panel import SettingsPanel

from .spotify_panel import SpotifyPanel
from .backup_panel import BackupPanel

class MainWindow(QMainWindow):
    """Main window for the Music Indexer application."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Initialize application components
        self.config_manager = ConfigManager()
        self.music_indexer = MusicIndexer()

        # Set up application logging
        self.setup_logging()
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_window_settings()
        
        # Set up a timer to keep UI responsive
        from PyQt5.QtCore import QTimer
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.process_events)
        self.ui_timer.start(100)  # 100ms interval
        
        logger.info("Main window initialized")

        # Add this at the end of __init__, after initializing UI
        self.load_saved_theme()        

    def setup_logging(self):
        """Set up application-wide logging."""
        # Get root logger
        root_logger = logging.getLogger()
        
        # Set global log level
        log_level = self.config_manager.get("app", "log_level", "INFO")
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        root_logger.setLevel(numeric_level)
        
        # Log application startup
        logger.info(f"Music Indexer v{self.config_manager.get('app', 'version', '0.1.0')} starting up")
        logger.info(f"Log level set to: {log_level}")
        
    def process_events(self):
        """Process pending events to keep UI responsive."""
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()
    
    def init_ui(self):
        """Initialize the user interface."""
        from PyQt5.QtWidgets import QDesktopWidget
        # Set window properties
        self.setWindowTitle("Music Indexer")
        self.setMinimumSize(900, 600)
        
        # Set window size to 80% of screen width and height
        screen = QDesktopWidget().screenGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.resize(width, height)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.search_panel = SearchPanel(self.music_indexer)
        self.results_panel = EnhancedResultsPanel(self.music_indexer)
        self.settings_panel = SettingsPanel(self.music_indexer)
        self.spotify_panel = SpotifyPanel(self.music_indexer)
        self.backup_panel = BackupPanel(self.music_indexer)
        
        # Connect panels
        self.search_panel.search_completed.connect(self.results_panel.set_results)
        
        # Add tabs
        self.tab_widget.addTab(self.search_panel, "Search")
        self.tab_widget.addTab(self.results_panel, "Results")
        self.tab_widget.addTab(self.settings_panel, "Settings")
        self.tab_widget.addTab(self.spotify_panel, "Spotify")
        self.tab_widget.addTab(self.backup_panel, "Backup")
        
        # Create button layout
        button_layout = QHBoxLayout()

        self.extract_metadata_checkbox = QCheckBox("Extract Audio Metadata")
        self.extract_metadata_checkbox.setChecked(True)
        self.extract_metadata_checkbox.setToolTip(
            "When checked, full audio analysis is performed (duration, quality, etc.).\n"
            "Uncheck for faster indexing without audio analysis."
        )
        button_layout.addWidget(self.extract_metadata_checkbox)
   
        # Create action buttons
        self.index_button = QPushButton("Index Files")
        self.index_button.clicked.connect(self.start_indexing)
        
        self.clear_cache_button = QPushButton("Clear Cache")
        self.clear_cache_button.clicked.connect(self.clear_cache)
        
        # Add buttons to layout
        button_layout.addWidget(self.index_button)
        button_layout.addWidget(self.clear_cache_button)
        button_layout.addStretch()
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Update status with cache info
        self.update_status()
        
        # Create menus
        self.create_menus()
    
    def create_menus(self):
        """Create application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # Index action
        index_action = QAction("&Index Files", self)
        index_action.setShortcut("Ctrl+I")
        index_action.triggered.connect(self.start_indexing)
        file_menu.addAction(index_action)
        
        # Add directory action
        add_dir_action = QAction("&Add Directory", self)
        add_dir_action.triggered.connect(self.add_directory)
        file_menu.addAction(add_dir_action)
        
        file_menu.addSeparator()
        
        # Export results action
        export_action = QAction("&Export Results", self)
        export_action.triggered.connect(self.results_panel.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        
        # Clear cache action
        clear_cache_action = QAction("&Clear Cache", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        edit_menu.addAction(clear_cache_action)
        
        # Preferences action
        preferences_action = QAction("&Preferences", self)
        preferences_action.triggered.connect(lambda: self.tab_widget.setCurrentWidget(self.settings_panel))
        edit_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def update_status(self):
        """Update status bar with cache information."""
        try:
            stats = self.music_indexer.get_cache_stats()
            
            if stats['total_files'] > 0:
                formats = ', '.join([f"{fmt}: {count}" for fmt, count in stats['formats'].items()])
                status_text = (f"Indexed: {stats['total_files']} files, "
                               f"{stats['total_hours']:.2f} hours | {formats}")
                self.status_bar.showMessage(status_text)
            else:
                self.status_bar.showMessage("No files indexed. Click 'Index Files' to start.")
        
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            self.status_bar.showMessage("Error updating cache status")
    
    def start_indexing(self):
        """Start indexing files."""
        # Check if directories are configured
        directories = self.music_indexer.get_music_directories()
        
        if not directories:
            QMessageBox.warning(
                self,
                "No Directories",
                "No music directories are configured. Please add directories in Settings."
            )
            self.tab_widget.setCurrentWidget(self.settings_panel)
            return
        
        # Get metadata extraction setting
        extract_metadata = self.extract_metadata_checkbox.isChecked()
        
        # Create progress dialog (non-modal)
        self.progress_dialog = QProgressDialog(
            f"Indexing files with {'full' if extract_metadata else 'basic'} metadata extraction...", 
            "Cancel", 0, 100, self
        )
        self.progress_dialog.setWindowTitle("Indexing")
        self.progress_dialog.setWindowModality(Qt.NonModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        
        # Handle cancel button
        self.progress_dialog.canceled.connect(self.cancel_indexing)
        
        # Start indexing in background thread
        self.music_indexer.index_files_async(
            recursive=True,
            extract_metadata=extract_metadata,
            callback=self.update_index_progress,
            complete_callback=self.indexing_completed
        )
        
        # Show the dialog after starting the thread
        self.progress_dialog.show()
        
    def cancel_indexing(self):
        """Cancel indexing process."""
        if hasattr(self.music_indexer, '_current_worker'):
            self.music_indexer._current_worker.cancelled = True
        logger.info("Indexing cancelled by user")

    def update_index_progress(self, value, message):
        """Update indexing progress dialog."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(int(value))
            self.progress_dialog.setLabelText(message)

    def indexing_completed(self, success):
        """Handle indexing completion."""
        # Close progress dialog
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        
        if success:
            self.update_status()
            QMessageBox.information(
                self,
                "Indexing Complete",
                "File indexing completed successfully."
            )
        else:
            QMessageBox.warning(
                self,
                "Indexing Failed",
                "File indexing failed or was cancelled. Check logs for details."
            )
    
    def add_directory(self):
        """Add a music directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Music Directory",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            if self.music_indexer.add_music_directory(directory):
                self.settings_panel.update_directory_list()
                QMessageBox.information(
                    self,
                    "Directory Added",
                    f"Added directory: {directory}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Failed to Add Directory",
                    f"Failed to add directory: {directory}"
                )
    
    def clear_cache(self):
        """Clear the file cache."""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Are you sure you want to clear the cache? This will remove all indexed file information.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.music_indexer.clear_cache():
                self.update_status()
                QMessageBox.information(
                    self,
                    "Cache Cleared",
                    "Cache cleared successfully."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Failed to Clear Cache",
                    "Failed to clear cache. Check logs for details."
                )
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Music Indexer",
            "Music Indexer 0.1.0\n\n"
            "A tool for indexing and searching music collections.\n\n"
            "Created as a Python learning project."
        )
    
    def load_window_settings(self):
        """Load window settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Window state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def save_window_settings(self):
        """Save window settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up logging handlers first
        if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'log_console'):
            self.search_panel.log_console.cleanup()
        
        # Explicitly shut down logging system
        import logging
        logging.shutdown()
        
        # Your existing code for saving settings
        self.save_window_settings()
        
        # Only then accept the event to close
        event.accept()

    def load_saved_theme(self):
        """Load and apply the saved theme."""
        from PyQt5.QtCore import QSettings
        settings = QSettings("MusicIndexer", "MusicIndexer")
        theme = settings.value("appearance/theme", "System Default")
        
        logger.info(f"Loading saved theme: {theme}")
        
        # Find the settings panel to apply the theme
        if hasattr(self, 'settings_panel'):
            self.settings_panel._apply_theme(theme)
            logger.info(f"Applied theme: {theme}")
        else:
            logger.warning("Settings panel not found, couldn't apply theme")

def run_application():
    """Run the Music Indexer application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Music Indexer")
    app.setOrganizationName("MusicIndexer")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_application()
