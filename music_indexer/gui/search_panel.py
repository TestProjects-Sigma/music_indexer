"""
Enhanced search panel GUI with optimized matcher option for the music indexer application.
"""
import os
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QRadioButton, QFileDialog,
    QComboBox, QSlider, QCheckBox, QMessageBox, QProgressDialog,
    QFrame, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings

from ..utils.logger import get_logger
logger = get_logger()

from .log_console import LogConsole


class SearchPanel(QWidget):
    """Enhanced search panel with optimized matcher option for the Music Indexer application."""
    
    # Custom signals
    search_completed = pyqtSignal(list)
    
    def __init__(self, music_indexer):
        """Initialize the enhanced search panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Enhanced search panel with optimized matcher initialized")
    
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
        
        # NEW: Enhanced auto search option
        self.enhanced_auto_search_radio = QRadioButton("Enhanced Auto Search (optimized for electronic music)")
        self.enhanced_auto_search_radio.toggled.connect(self.toggle_search_mode)
        self.enhanced_auto_search_radio.setToolTip(
            "Uses optimized matching algorithm specifically designed for electronic music.\n"
            "Better handling of remix information, multi-artist tracks, and format preferences."
        )
        
        search_mode_layout.addWidget(self.manual_search_radio)
        search_mode_layout.addWidget(self.auto_search_radio)
        search_mode_layout.addWidget(self.enhanced_auto_search_radio)
        
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
        
        # Similarity threshold (only for standard auto search)
        self.threshold_layout = QHBoxLayout()
        self.threshold_layout.addWidget(QLabel("Similarity Threshold:"))
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(75)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        self.threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel("75%")
        self.threshold_slider.valueChanged.connect(self._update_threshold_label)
        self.threshold_layout.addWidget(self.threshold_label)
        
        auto_search_layout.addLayout(self.threshold_layout)
        
        # Search algorithm info
        self.algorithm_info_label = QLabel("")
        self.algorithm_info_label.setWordWrap(True)
        self.algorithm_info_label.setStyleSheet("color: #666; font-style: italic; margin: 5px 0;")
        auto_search_layout.addWidget(self.algorithm_info_label)
        
        # Process button
        process_button_layout = QHBoxLayout()
        self.process_button = QPushButton("Process File")
        self.process_button.clicked.connect(self.perform_auto_search)
        process_button_layout.addStretch()
        process_button_layout.addWidget(self.process_button)
        auto_search_layout.addLayout(process_button_layout)
        
        main_layout.addWidget(self.auto_search_group)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Create log console section
        log_section = QWidget(self)
        log_layout = QVBoxLayout(log_section)
        
        # Add a header for the log section
        log_header = QHBoxLayout()
        log_title = QLabel("Application Log")
        log_title.setStyleSheet("font-weight: bold;")
        log_header.addWidget(log_title)
        log_header.addStretch()
        log_layout.addLayout(log_header)
        
        # Create log console
        self.log_console = LogConsole(log_section)
        log_layout.addWidget(self.log_console)
        
        # Add log section to main layout
        main_layout.addWidget(log_section)
        
        # Log initial message
        logger.info("Enhanced search panel initialized with optimized matcher support")
        
        # Set initial state
        self.toggle_search_mode()
    
    def toggle_search_mode(self):
        """Toggle between manual, automatic, and enhanced automatic search modes."""
        manual_mode = self.manual_search_radio.isChecked()
        auto_mode = self.auto_search_radio.isChecked() or self.enhanced_auto_search_radio.isChecked()
        enhanced_mode = self.enhanced_auto_search_radio.isChecked()
        
        self.manual_search_group.setVisible(manual_mode)
        self.auto_search_group.setVisible(auto_mode)
        
        # Update algorithm info and threshold visibility
        if enhanced_mode:
            self.algorithm_info_label.setText(
                "🎵 Enhanced Algorithm: Optimized for electronic music with advanced remix detection,\n"
                "multi-artist handling, and format quality ranking. Uses fixed thresholds for consistency."
            )
            # Hide threshold slider for enhanced mode (it uses fixed optimized thresholds)
            for i in range(self.threshold_layout.count()):
                item = self.threshold_layout.itemAt(i)
                if item.widget():
                    item.widget().setVisible(False)
        elif auto_mode:
            self.algorithm_info_label.setText(
                "🔍 Standard Algorithm: General-purpose fuzzy matching with configurable threshold."
            )
            # Show threshold slider for standard auto search
            for i in range(self.threshold_layout.count()):
                item = self.threshold_layout.itemAt(i)
                if item.widget():
                    item.widget().setVisible(True)
        else:
            self.algorithm_info_label.setText("")
    
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
        
        # Determine which algorithm to use
        use_enhanced = self.enhanced_auto_search_radio.isChecked()
        
        # Create progress dialog
        algorithm_name = "Enhanced" if use_enhanced else "Standard"
        self.auto_progress = QProgressDialog(f"Processing with {algorithm_name} algorithm...", "Cancel", 0, 100, self)
        self.auto_progress.setWindowTitle("Processing")
        self.auto_progress.setWindowModality(Qt.NonModal)
        self.auto_progress.setMinimumDuration(0)
        self.auto_progress.setAutoClose(False)
        self.auto_progress.setAutoReset(False)
        
        # Create worker using Qt's thread pool
        from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
        
        class AutoSearchWorker(QRunnable):
            """Worker for automatic search in a separate thread."""
            
            class Signals(QObject):
                """Worker signals."""
                progress = pyqtSignal(float, str)
                finished = pyqtSignal(list)
                
            def __init__(self, music_indexer, match_file, use_enhanced):
                """Initialize the worker."""
                super().__init__()
                self.music_indexer = music_indexer
                self.match_file = match_file
                self.use_enhanced = use_enhanced
                self.signals = self.Signals()
                self.cancelled = False
            
            @pyqtSlot()
            def run(self):
                """Run the worker."""
                try:
                    if self.use_enhanced:
                        # Use optimized matcher
                        from ..search.optimized_matcher import OptimizedMatcher
                        matcher = OptimizedMatcher(self.music_indexer.cache_manager, self.music_indexer.config_manager)
                        results = matcher.process_match_file(self.match_file, show_progress=False)
                    else:
                        # Use standard auto search
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
        worker = AutoSearchWorker(self.music_indexer, match_file, use_enhanced)
        
        # Connect signals
        worker.signals.finished.connect(self.auto_search_completed)
        
        # Handle cancel button
        self.auto_progress.canceled.connect(lambda: setattr(worker, 'cancelled', True))
        
        # Start worker
        QThreadPool.globalInstance().start(worker)
        
        # Show the dialog after starting the thread
        self.auto_progress.show()
        
        # Log which algorithm is being used
        algorithm_name = "Enhanced (Optimized)" if use_enhanced else "Standard"
        logger.info(f"Starting {algorithm_name} automatic search: {match_file}")

    def auto_search_completed(self, results):
        """Handle automatic search completion."""
        # Close progress dialog
        if hasattr(self, 'auto_progress') and self.auto_progress:
            self.auto_progress.close()
        
        algorithm_name = "Enhanced" if self.enhanced_auto_search_radio.isChecked() else "Standard"
        
        if results:
            # Emit results directly
            self.search_completed.emit(results)
            
            # Count matches
            total_matches = sum(len(result.get('matches', [])) for result in results)
            missing_entries = sum(1 for result in results if not result.get('matches', []))
            
            logger.info(
                f"{algorithm_name} automatic search completed: processed {len(results)} entries, "
                f"found {total_matches} matches, {missing_entries} entries with no matches"
            )
            
            # Show enhanced summary for optimized matcher
            if self.enhanced_auto_search_radio.isChecked():
                # Calculate additional statistics for enhanced algorithm
                perfect_matches = 0
                high_quality_matches = 0
                
                for result in results:
                    matches = result.get('matches', [])
                    if matches:
                        best_match = matches[0]
                        score = best_match.get('match_score', 0)
                        strategy = best_match.get('strategy', '')
                        
                        if 'perfect_remix_match' in strategy:
                            perfect_matches += 1
                        elif score >= 90:
                            high_quality_matches += 1
                
                QMessageBox.information(
                    self,
                    "Enhanced Processing Complete",
                    f"🎵 Enhanced Algorithm Results:\n\n"
                    f"📊 Processed: {len(results)} entries\n"
                    f"✅ Found matches: {len(results) - missing_entries}\n"
                    f"🎯 Perfect remix matches: {perfect_matches}\n"
                    f"⭐ High quality matches (90%+): {high_quality_matches}\n"
                    f"❌ Missing entries: {missing_entries}\n\n"
                    f"🔧 The enhanced algorithm provides better ranking\n"
                    f"for electronic music with remix information."
                )
            else:
                # Standard summary
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
                f"{algorithm_name} processing failed. Check logs for details."
            )
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load search mode
        search_mode = settings.value("search/mode", "manual")
        if search_mode == "enhanced_auto":
            self.enhanced_auto_search_radio.setChecked(True)
        elif search_mode == "auto":
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
        if self.enhanced_auto_search_radio.isChecked():
            search_mode = "enhanced_auto"
        elif self.auto_search_radio.isChecked():
            search_mode = "auto"
        else:
            search_mode = "manual"
        settings.setValue("search/mode", search_mode)
        
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
                        