"""
Search panel GUI for the music indexer application.
"""
import os
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QRadioButton, QFileDialog,
    QComboBox, QSlider, QCheckBox, QMessageBox, QProgressDialog,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings

from ..utils.logger import get_logger

logger = get_logger()

from .log_console import LogConsole

class SearchPanel(QWidget):
    """Search panel for the Music Indexer application."""
    
    # Custom signals
    search_completed = pyqtSignal(list)
    
    def __init__(self, music_indexer):
        """Initialize the search panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Search panel initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create search mode group
        search_mode_group = QGroupBox("Search Mode")
        search_mode_layout = QVBoxLayout(search_mode_group)
        
        # Create radio buttons for search mode
        self.manual_search_radio = QRadioButton("Manual Search")
        self.manual_search_radio.setChecked(True)
        self.manual_search_radio.toggled.connect(self.toggle_search_mode)
        
        self.auto_search_radio = QRadioButton("Automatic Search (from file)")
        self.auto_search_radio.toggled.connect(self.toggle_search_mode)
        
        search_mode_layout.addWidget(self.manual_search_radio)
        search_mode_layout.addWidget(self.auto_search_radio)
        
        main_layout.addWidget(search_mode_group)
        
        # Create manual search options
        self.manual_search_group = QGroupBox("Manual Search Options")
        manual_search_layout = QVBoxLayout(self.manual_search_group)
        
        # Query fields
        form_layout = QVBoxLayout()
        
        # General query
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("General Query:"))
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Search across all fields")
        query_layout.addWidget(self.query_input)
        form_layout.addLayout(query_layout)
        
        # Artist
        artist_layout = QHBoxLayout()
        artist_layout.addWidget(QLabel("Artist:"))
        self.artist_input = QLineEdit()
        artist_layout.addWidget(self.artist_input)
        form_layout.addLayout(artist_layout)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        title_layout.addWidget(self.title_input)
        form_layout.addLayout(title_layout)
        
        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("Any")
        for fmt in ["mp3", "flac", "m4a", "aac", "wav"]:
            self.format_combo.addItem(fmt)
        format_layout.addWidget(self.format_combo)
        form_layout.addLayout(format_layout)
        
        # Search options
        options_layout = QHBoxLayout()
        
        self.exact_match_checkbox = QCheckBox("Exact Match")
        self.exact_match_checkbox.setToolTip("Use exact matching instead of fuzzy matching")
        options_layout.addWidget(self.exact_match_checkbox)
        
        options_layout.addStretch()
        
        form_layout.addLayout(options_layout)
        
        manual_search_layout.addLayout(form_layout)
        
        # Search button
        search_button_layout = QHBoxLayout()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_manual_search)
        search_button_layout.addStretch()
        search_button_layout.addWidget(self.search_button)
        manual_search_layout.addLayout(search_button_layout)
        
        main_layout.addWidget(self.manual_search_group)
        
        # Create automatic search options
        self.auto_search_group = QGroupBox("Automatic Search Options")
        auto_search_layout = QVBoxLayout(self.auto_search_group)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Match File:"))
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        file_layout.addWidget(self.file_input)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_match_file)
        file_layout.addWidget(self.browse_button)
        
        auto_search_layout.addLayout(file_layout)
        
        # Similarity threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Similarity Threshold:"))
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(75)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel("75%")
        self.threshold_slider.valueChanged.connect(self._update_threshold_label)
        threshold_layout.addWidget(self.threshold_label)
        
        auto_search_layout.addLayout(threshold_layout)
        
        # Process button
        process_button_layout = QHBoxLayout()
        self.process_button = QPushButton("Process File")
        self.process_button.clicked.connect(self.perform_auto_search)
        process_button_layout.addStretch()
        process_button_layout.addWidget(self.process_button)
        auto_search_layout.addLayout(process_button_layout)
        
        main_layout.addWidget(self.auto_search_group)

        # Add a separator line (optional)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Create and add log console
        self.log_console = LogConsole()
        main_layout.addWidget(self.log_console)

        # Log message to show console is active
        logging.info("Search panel initialized. Ready for search queries.")

        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        # Set initial state
        self.toggle_search_mode()
    
    def toggle_search_mode(self):
        """Toggle between manual and automatic search modes."""
        manual_mode = self.manual_search_radio.isChecked()
        self.manual_search_group.setVisible(manual_mode)
        self.auto_search_group.setVisible(not manual_mode)
    
    def _update_threshold_label(self, value):
        """Update threshold label when slider value changes."""
        self.threshold_label.setText(f"{value}%")
        self.music_indexer.set_similarity_threshold(value)
    
    def browse_match_file(self):
        """Browse for a match file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Match File",
            os.path.expanduser("~"),
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            self.file_input.setText(file_path)
    
    def perform_manual_search(self):
        """Perform manual search."""
        # Get search parameters
        query = self.query_input.text().strip()
        artist = self.artist_input.text().strip()
        title = self.title_input.text().strip()
        format_type = self.format_combo.currentText()
        
        if format_type == "Any":
            format_type = None
        
        exact_match = self.exact_match_checkbox.isChecked()
        
        # Check if at least one search field is filled
        if not any([query, artist, title, format_type]):
            QMessageBox.warning(
                self,
                "Empty Search",
                "Please enter at least one search term."
            )
            return
        
        # Perform search
        results = self.music_indexer.search_files(
            query=query,
            artist=artist,
            title=title,
            format_type=format_type,
            exact_match=exact_match
        )
        
        # Emit results
        self.search_completed.emit(results)
        
        # Log search
        logger.info(
            f"Manual search performed: query='{query}', artist='{artist}', "
            f"title='{title}', format='{format_type}', exact={exact_match}"
        )
        
        # Show message if no results
        if not results:
            QMessageBox.information(
                self,
                "No Results",
                "No matching files found."
            )
    
    def perform_auto_search(self):
        """Perform automatic search from match file."""
        # Get match file
        match_file = self.file_input.text()
        
        if not match_file or not os.path.exists(match_file):
            QMessageBox.warning(
                self,
                "Invalid Match File",
                "Please select a valid match file."
            )
            return
        
        # Create progress dialog (non-modal)
        self.auto_progress = QProgressDialog("Processing match file...", "Cancel", 0, 100, self)
        self.auto_progress.setWindowTitle("Processing")
        self.auto_progress.setWindowModality(Qt.NonModal)
        self.auto_progress.setMinimumDuration(0)
        self.auto_progress.setAutoClose(False)
        self.auto_progress.setAutoReset(False)
        
        # Create a worker using Qt's thread pool
        from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
        
        class AutoSearchWorker(QRunnable):
            """Worker for automatic search in a separate thread."""
            
            class Signals(QObject):
                """Worker signals."""
                progress = pyqtSignal(float, str)
                finished = pyqtSignal(list)
                
            def __init__(self, music_indexer, match_file):
                """Initialize the worker."""
                super().__init__()
                self.music_indexer = music_indexer
                self.match_file = match_file
                self.signals = self.Signals()
                self.cancelled = False
            
            @pyqtSlot()
            def run(self):
                """Run the worker."""
                try:
                    # Process match file
                    results = self.music_indexer.process_match_file(
                        self.match_file, 
                        show_progress=False
                    )
                    
                    # Emit finished signal with results
                    self.signals.finished.emit(results)
                
                except Exception as e:
                    logger.error(f"Error in auto search worker: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    self.signals.finished.emit([])
        
        # Create worker
        worker = AutoSearchWorker(self.music_indexer, match_file)
        
        # Connect signals
        worker.signals.finished.connect(self.auto_search_completed)
        
        # Handle cancel button
        self.auto_progress.canceled.connect(lambda: setattr(worker, 'cancelled', True))
        
        # Start worker
        QThreadPool.globalInstance().start(worker)
        
        # Show the dialog after starting the thread
        self.auto_progress.show()

    def auto_search_completed(self, results):
        """Handle automatic search completion."""
        # Close progress dialog
        if hasattr(self, 'auto_progress') and self.auto_progress:
            self.auto_progress.close()
        
        if results:
            # Emit results directly - now our ResultsPanel knows how to handle this format
            self.search_completed.emit(results)
            
            # Count matches
            total_matches = sum(len(result.get('matches', [])) for result in results)
            missing_entries = sum(1 for result in results if not result.get('matches', []))
            
            logger.info(
                f"Automatic search completed: processed {len(results)} entries, "
                f"found {total_matches} matches, {missing_entries} entries with no matches"
            )
            
            # Show summary
            QMessageBox.information(
                self,
                "Processing Complete",
                f"Processed {len(results)} entries from match file.\n"
                f"Found {total_matches} matching files.\n"
                f"Entries with no matches: {missing_entries}"
            )
        else:
            QMessageBox.warning(
                self,
                "Processing Failed",
                "Failed to process match file. Check logs for details."
            )
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load search mode
        if settings.value("search/auto_mode", False, type=bool):
            self.auto_search_radio.setChecked(True)
        else:
            self.manual_search_radio.setChecked(True)
        
        # Load threshold
        threshold = settings.value("search/threshold", 75, type=int)
        self.threshold_slider.setValue(threshold)
        
        # Load match file
        match_file = settings.value("search/match_file", "")
        if match_file and os.path.exists(match_file):
            self.file_input.setText(match_file)
        
        # Load exact match
        exact_match = settings.value("search/exact_match", False, type=bool)
        self.exact_match_checkbox.setChecked(exact_match)
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save search mode
        settings.setValue("search/auto_mode", self.auto_search_radio.isChecked())
        
        # Save threshold
        settings.setValue("search/threshold", self.threshold_slider.value())
        
        # Save match file
        match_file = self.file_input.text()
        if match_file and os.path.exists(match_file):
            settings.setValue("search/match_file", match_file)
        
        # Save exact match
        settings.setValue("search/exact_match", self.exact_match_checkbox.isChecked())
    
    def closeEvent(self, event):
        """Handle panel close event."""
        self.save_settings()
        super().closeEvent(event)
