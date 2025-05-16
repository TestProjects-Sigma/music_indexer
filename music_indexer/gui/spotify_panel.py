"""
Spotify integration panel for the music indexer application.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QCheckBox, QFileDialog,
    QProgressBar, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread

# Import the Spotify Playlist Extractor
from ..utils.spotify_playlist_extractor import SpotifyPlaylistExtractor
from ..utils.logger import get_logger

logger = get_logger()


class WorkerSignals(QObject):
    """Defines signals available for the Spotify extraction worker thread."""
    update_status = pyqtSignal(bool, str)
    finished = pyqtSignal(bool, str)


class SpotifyExtractionWorker(QThread):
    """Worker thread for Spotify playlist extraction."""
    
    def __init__(self, extractor, playlist_url, output_file):
        super().__init__()
        self.extractor = extractor
        self.playlist_url = playlist_url
        self.output_file = output_file
        self.signals = WorkerSignals()
    
    def run(self):
        """Run the extraction process."""
        def callback(success, message):
            self.signals.update_status.emit(success, message)
        
        success, message = self.extractor.extract_playlist(
            self.playlist_url,
            self.output_file,
            callback=callback
        )
        
        self.signals.finished.emit(success, message)


class SpotifyPanel(QWidget):
    """Spotify integration panel for the Music Indexer application."""
    
    def __init__(self, music_indexer):
        """Initialize the Spotify panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        # Pass the config_manager to the extractor
        self.extractor = SpotifyPlaylistExtractor(
            config_manager=self.music_indexer.config_manager
        )
        self.extraction_worker = None
        
        # Set up UI
        self.init_ui()
        
        logger.info("Spotify panel initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Spotify Playlist Extractor")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Description
        description_label = QLabel(
            "Extract tracks from a Spotify playlist and save them to a text file.\n"
            "The text file can then be used for automatic search in the Music Indexer."
        )
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)
        
        # Add some spacing
        main_layout.addSpacing(10)
        
        # Playlist URL
        url_group = QGroupBox("Spotify Playlist")
        url_layout = QVBoxLayout(url_group)
        
        url_description = QLabel("Enter the URL of the Spotify playlist you want to extract:")
        url_layout.addWidget(url_description)
        
        url_input_layout = QHBoxLayout()
        url_label = QLabel("Playlist URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://open.spotify.com/playlist/...")
        
        url_input_layout.addWidget(url_label)
        url_input_layout.addWidget(self.url_input)
        url_layout.addLayout(url_input_layout)
        
        main_layout.addWidget(url_group)
        
        # Output file selection
        output_group = QGroupBox("Output File")
        output_layout = QVBoxLayout(output_group)
        
        output_description = QLabel(
            "Select where to save the extracted playlist.\n"
            "This file can be used later for automatic search in the Music Indexer."
        )
        output_description.setWordWrap(True)
        output_layout.addWidget(output_description)
        
        output_input_layout = QHBoxLayout()
        output_label = QLabel("Output File:")
        self.output_input = QLineEdit()
        
        # Get default export directory from config
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if default_dir and os.path.exists(default_dir):
            default_path = os.path.join(default_dir, "spotify_playlist.txt")
            self.output_input.setText(default_path)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_output_file)
        
        output_input_layout.addWidget(output_label)
        output_input_layout.addWidget(self.output_input)
        output_input_layout.addWidget(browse_button)
        output_layout.addLayout(output_input_layout)
        
        main_layout.addWidget(output_group)
        
        # Spotify API credentials
        creds_group = QGroupBox("Spotify API Credentials")
        creds_layout = QVBoxLayout(creds_group)
        
        creds_description = QLabel(
            "You need Spotify API credentials to extract playlists.\n"
            "If you don't have credentials, create them at: https://developer.spotify.com/dashboard/"
        )
        creds_description.setWordWrap(True)
        creds_layout.addWidget(creds_description)
        
        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_label = QLabel("Client ID:")
        self.client_id_input = QLineEdit()
        if self.extractor.client_id:
            self.client_id_input.setText(self.extractor.client_id)
        
        client_id_layout.addWidget(client_id_label)
        client_id_layout.addWidget(self.client_id_input)
        creds_layout.addLayout(client_id_layout)
        
        # Client Secret
        client_secret_layout = QHBoxLayout()
        client_secret_label = QLabel("Client Secret:")
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        if self.extractor.client_secret:
            self.client_secret_input.setText(self.extractor.client_secret)
        
        client_secret_layout.addWidget(client_secret_label)
        client_secret_layout.addWidget(self.client_secret_input)
        creds_layout.addLayout(client_secret_layout)
        
        # Remember credentials
        self.remember_checkbox = QCheckBox("Remember these credentials")
        self.remember_checkbox.setChecked(True)
        creds_layout.addWidget(self.remember_checkbox)
        
        main_layout.addWidget(creds_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.extract_button = QPushButton("Extract Playlist")
        self.extract_button.clicked.connect(self.start_extraction)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_extraction)
        self.cancel_button.setEnabled(False)
        
        buttons_layout.addWidget(self.extract_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)
        
        # Status and progress
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(status_layout)
        
        # Add help text about using the extracted file
        help_frame = QFrame()
        help_frame.setFrameShape(QFrame.StyledPanel)
        help_frame.setStyleSheet("background-color: #f0f0f0;")
        help_layout = QVBoxLayout(help_frame)
        
        help_title = QLabel("How to use the extracted playlist")
        help_title.setStyleSheet("font-weight: bold;")
        help_layout.addWidget(help_title)
        
        help_text = QLabel(
            "1. Extract your Spotify playlist to a text file\n"
            "2. Go to the 'Search' tab and select 'Automatic Search'\n"
            "3. Browse and select your extracted file\n"
            "4. Click 'Process File' to find matches in your music collection"
        )
        help_layout.addWidget(help_text)
        
        main_layout.addWidget(help_frame)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
    
    def browse_output_file(self):
        """Browse for output file."""
        # Get default export directory from config
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
        
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Playlist As",
            os.path.join(default_dir, "spotify_playlist.txt"),
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            self.output_input.setText(file_path)
    
    def update_status(self, success, message):
        """Update status from extraction process."""
        self.status_label.setText(message)
    
    def start_extraction(self):
        """Start playlist extraction."""
        # Get inputs
        playlist_url = self.url_input.text().strip()
        output_file = self.output_input.text().strip()
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        remember_credentials = self.remember_checkbox.isChecked()
        
        # Validate inputs
        if not playlist_url:
            QMessageBox.warning(self, "Missing Input", "Please enter a Spotify playlist URL")
            return
        
        if not output_file:
            QMessageBox.warning(self, "Missing Input", "Please select an output file")
            return
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Missing Input", "Please enter your Spotify API credentials")
            return
        
        # Update extractor credentials
        self.extractor.client_id = client_id
        self.extractor.client_secret = client_secret
        
        # Save credentials if requested
        if remember_credentials:
            client_id = self.client_id_input.text().strip()
            client_secret = self.client_secret_input.text().strip()
            success = self.extractor.save_credentials(client_id, client_secret)
            if not success:
                logger.warning("Failed to save Spotify credentials")
        
        # Update UI
        self.extract_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.status_label.setText("Starting extraction...")
        
        # Create and start worker thread
        self.extraction_worker = SpotifyExtractionWorker(
            self.extractor, playlist_url, output_file
        )
        self.extraction_worker.signals.update_status.connect(self.update_status)
        self.extraction_worker.signals.finished.connect(self.extraction_finished)
        self.extraction_worker.start()

        from PyQt5.QtWidgets import QScrollArea
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Add all your content to main_layout
        
        # Set the main widget as the scroll area's widget
        scroll_area.setWidget(main_widget)
        
        # Create the panel's main layout and add the scroll area
        panel_layout = QVBoxLayout(self)
        panel_layout.addWidget(scroll_area)
    
    def extraction_finished(self, success, message):
        """Handle extraction completion."""
        # Update UI
        self.extract_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText(message)
        
        # Show message
        if success:
            output_file = self.output_input.text().strip()
            QMessageBox.information(
                self,
                "Extraction Complete",
                f"{message}\n\nTo search for these tracks:\n1. Go to the 'Search' tab\n2. Select 'Automatic Search'\n3. Select the file: {output_file}\n4. Click 'Process File'"
            )
        else:
            QMessageBox.warning(self, "Extraction Failed", message)
    
    def cancel_extraction(self):
        """Cancel ongoing extraction."""
        if self.extractor and self.extraction_worker:
            self.extractor.cancel_extraction()
            self.status_label.setText("Cancelling extraction...")
    
    def load_into_search(self, file_path):
        """Load the extracted playlist into the search tab."""
        try:
            # Find the main window
            from PyQt5.QtWidgets import QApplication
            main_window = QApplication.instance().activeWindow()
            
            # Find the search panel tab
            tab_widget = main_window.tab_widget
            
            # Loop through tabs to find the search panel
            for i in range(tab_widget.count()):
                if tab_widget.tabText(i) == "Search":
                    search_tab = tab_widget.widget(i)
                    tab_widget.setCurrentIndex(i)
                    break
            else:
                logger.error("Could not find Search tab")
                return
            
            # Now that we have the search panel, set it up for automatic search
            try:
                # Switch to auto search mode if we can find the radio button
                auto_search_radio = search_tab.findChild(QRadioButton, "auto_search_radio")
                if auto_search_radio:
                    auto_search_radio.setChecked(True)
                
                # Set the file path if we can find the input field
                file_input = search_tab.findChild(QLineEdit, "file_input")
                if file_input:
                    file_input.setText(file_path)
                
                # Try to trigger the mode toggle
                if hasattr(search_tab, "toggle_search_mode"):
                    search_tab.toggle_search_mode()
                
                logger.info(f"Loaded extracted playlist into search: {file_path}")
            except Exception as e:
                logger.error(f"Error setting up search tab: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error switching to search tab: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
