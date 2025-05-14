"""
Settings panel GUI for the music indexer application.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QGroupBox, QSlider, QFileDialog, QMessageBox,
    QCheckBox, QSpinBox, QComboBox, QFormLayout, QLineEdit  # Add QLineEdit here
)
from PyQt5.QtCore import Qt, QSettings

from ..utils.logger import get_logger

logger = get_logger()


class SettingsPanel(QWidget):
    """Settings panel for the Music Indexer application."""
    
    def __init__(self, music_indexer):
        """Initialize the settings panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Settings panel initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create directories group
        directories_group = QGroupBox("Music Directories")
        directories_layout = QVBoxLayout(directories_group)
        
        # Create directory list
        self.directory_list = QListWidget()
        directories_layout.addWidget(self.directory_list)
        
        # Create directory buttons
        dir_buttons_layout = QHBoxLayout()
        
        self.add_dir_button = QPushButton("Add Directory")
        self.add_dir_button.clicked.connect(self.add_directory)
        dir_buttons_layout.addWidget(self.add_dir_button)
        
        self.remove_dir_button = QPushButton("Remove Directory")
        self.remove_dir_button.clicked.connect(self.remove_directory)
        self.remove_dir_button.setEnabled(False)
        dir_buttons_layout.addWidget(self.remove_dir_button)
        
        directories_layout.addLayout(dir_buttons_layout)
        
        # Add directories group to main layout
        main_layout.addWidget(directories_group)
        
        # Create export directory group
        export_group = QGroupBox("Export Settings")
        export_layout = QHBoxLayout(export_group)
        
        # Create export directory field
        export_layout.addWidget(QLabel("Default Export Directory:"))
        self.export_dir_input = QLineEdit()
        self.export_dir_input.setReadOnly(True)
        export_layout.addWidget(self.export_dir_input)
        
        # Create export directory button
        self.export_dir_button = QPushButton("Browse")
        self.export_dir_button.clicked.connect(self.browse_export_directory)
        export_layout.addWidget(self.export_dir_button)
        
        # Add export group to main layout
        main_layout.addWidget(export_group)
        
        # Create search settings group
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)
        
        # Create similarity threshold slider
        threshold_layout = QHBoxLayout()
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(75)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel("75%")
        self.threshold_slider.valueChanged.connect(self._update_threshold_label)
        threshold_layout.addWidget(self.threshold_label)
        
        search_layout.addRow("Similarity Threshold:", threshold_layout)
        
        # Create recursive scan checkbox
        self.recursive_scan_checkbox = QCheckBox("Scan Subdirectories")
        self.recursive_scan_checkbox.setChecked(True)
        search_layout.addRow("", self.recursive_scan_checkbox)
        
        # Add search group to main layout
        main_layout.addWidget(search_group)
        
        # Create file format group
        format_group = QGroupBox("File Formats")
        format_layout = QVBoxLayout(format_group)
        
        # Create format checkboxes
        self.format_checkboxes = {}
        for fmt in ["mp3", "flac", "m4a", "aac", "wav"]:
            checkbox = QCheckBox(fmt.upper())
            checkbox.setChecked(True)
            format_layout.addWidget(checkbox)
            self.format_checkboxes[fmt] = checkbox
        
        # Add format group to main layout
        main_layout.addWidget(format_group)
        
        # Create appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        # Create theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("System Default")
        self.theme_combo.addItem("Light")
        self.theme_combo.addItem("Dark")
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        # Add appearance group to main layout
        main_layout.addWidget(appearance_group)
        
        # Create save settings button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        # Update directory list
        self.update_directory_list()
        
        # Connect signals
        self.directory_list.itemSelectionChanged.connect(self._update_dir_buttons)

    def browse_export_directory(self):
        """Browse for default export directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Export Directory",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.export_dir_input.setText(directory)
    
    def _update_threshold_label(self, value):
        """Update threshold label when slider value changes."""
        self.threshold_label.setText(f"{value}%")
        self.music_indexer.set_similarity_threshold(value)
    
    def _update_dir_buttons(self):
        """Update directory button states based on selection."""
        self.remove_dir_button.setEnabled(self.directory_list.currentItem() is not None)
    
    def update_directory_list(self):
        """Update the directory list widget."""
        # Clear list
        self.directory_list.clear()
        
        # Get configured directories
        directories = self.music_indexer.get_music_directories()
        
        # Add directories to list
        for directory in directories:
            self.directory_list.addItem(directory)
        
        # Update button states
        self._update_dir_buttons()
    
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
                self.update_directory_list()
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
    
    def remove_directory(self):
        """Remove selected music directory."""
        current_item = self.directory_list.currentItem()
        
        if not current_item:
            return
        
        directory = current_item.text()
        
        reply = QMessageBox.question(
            self,
            "Remove Directory",
            f"Are you sure you want to remove the following directory?\n{directory}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.music_indexer.remove_music_directory(directory):
                self.update_directory_list()
            else:
                QMessageBox.warning(
                    self,
                    "Failed to Remove Directory",
                    f"Failed to remove directory: {directory}"
                )
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load threshold
        threshold = settings.value("search/threshold", 75, type=int)
        self.threshold_slider.setValue(threshold)
        
        # Load recursive scan
        recursive = settings.value("indexing/recursive", True, type=bool)
        self.recursive_scan_checkbox.setChecked(recursive)
        
        # Load formats
        supported_formats = self.music_indexer.config_manager.get_supported_formats()
        for fmt, checkbox in self.format_checkboxes.items():
            checkbox.setChecked(fmt in supported_formats)
        
        # Load export directory
        export_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        self.export_dir_input.setText(export_dir)
        
        # Load theme
        theme = settings.value("appearance/theme", "System Default")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save threshold
        threshold = self.threshold_slider.value()
        settings.setValue("search/threshold", threshold)
        self.music_indexer.set_similarity_threshold(threshold)
        
        # Save recursive scan
        recursive = self.recursive_scan_checkbox.isChecked()
        settings.setValue("indexing/recursive", recursive)
        
        # Save formats
        supported_formats = []
        for fmt, checkbox in self.format_checkboxes.items():
            if checkbox.isChecked():
                supported_formats.append(fmt)
        
        self.music_indexer.config_manager.set("indexing", "supported_formats", supported_formats)
        
        # Save export directory
        export_dir = self.export_dir_input.text()
        self.music_indexer.config_manager.set("paths", "default_export_directory", export_dir)
        
        # Save theme
        theme = self.theme_combo.currentText()
        settings.setValue("appearance/theme", theme)
        self._apply_theme(theme)
        
        QMessageBox.information(
            self,
            "Settings Saved",
            "Settings saved successfully. Some changes may require restarting the application."
        )
    
    def _apply_theme(self, theme):
        """Apply the selected theme."""
        # This is a simplified implementation
        # In a real application, you would use QSS (Qt Style Sheets) to apply themes
        pass
    
    def closeEvent(self, event):
        """Handle panel close event."""
        super().closeEvent(event)
