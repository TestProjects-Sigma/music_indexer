"""
Enhanced settings panel GUI with auto-selection preferences for the music indexer application.
Updated to use app root as default directory for browse buttons.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QGroupBox, QSlider, QFileDialog, QMessageBox,
    QCheckBox, QSpinBox, QComboBox, QFormLayout, QLineEdit,
    QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, QSettings

from ..utils.logger import get_logger

logger = get_logger()


class SettingsPanel(QWidget):
    """Enhanced settings panel for the Music Indexer application."""
    
    def __init__(self, music_indexer):
        """Initialize the settings panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Enhanced settings panel initialized")
    
    def get_app_root_directory(self):
        """
        Get the app root directory (where main.py is located).
        
        Returns:
            str: Path to app root directory
        """
        # Get the directory where main.py is located
        # Since we're in music_indexer/gui/settings_panel.py, we need to go up 2 levels
        current_file = os.path.abspath(__file__)
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        
        # Verify that main.py exists in this directory
        main_py_path = os.path.join(app_root, "main.py")
        if os.path.exists(main_py_path):
            return app_root
        else:
            # Fallback to current working directory if main.py not found
            logger.warning(f"main.py not found at {main_py_path}, using current working directory")
            return os.getcwd()
    
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
        main_layout.addWidget(directories_group)
        
        # Create export directory group
        export_group = QGroupBox("Export Settings")
        export_layout = QHBoxLayout(export_group)
        
        export_layout.addWidget(QLabel("Default Export Directory:"))
        self.export_dir_input = QLineEdit()
        self.export_dir_input.setReadOnly(True)
        export_layout.addWidget(self.export_dir_input)
        
        self.export_dir_button = QPushButton("Browse")
        self.export_dir_button.clicked.connect(self.browse_export_directory)
        export_layout.addWidget(self.export_dir_button)
        
        main_layout.addWidget(export_group)
        
        # Create search settings group
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)

        # Create suffix removal settings group
        suffix_group = QGroupBox("Advanced Search Settings")
        suffix_layout = QVBoxLayout(suffix_group)
        
        # Suffix removal configuration
        suffix_label = QLabel("Ignore Suffixes (comma-separated):")
        suffix_label.setToolTip("File suffixes to ignore when matching (e.g. justify, sob, nrg)")
        suffix_layout.addWidget(suffix_label)
        
        self.ignore_suffixes_input = QLineEdit()
        self.ignore_suffixes_input.setPlaceholderText("justify, sob, nrg, dps, trt, pms")
        self.ignore_suffixes_input.setToolTip(
            "Enter comma-separated suffixes to ignore during matching.\n"
            "Example: 'justify, sob, nrg' will make 'track-justify' match 'track'"
        )
        suffix_layout.addWidget(self.ignore_suffixes_input)
        
        # Info label
        suffix_info = QLabel("These suffixes will be removed from titles during matching to improve accuracy.")
        suffix_info.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        suffix_info.setWordWrap(True)
        suffix_layout.addWidget(suffix_info)
        
        main_layout.addWidget(suffix_group)

        # Similarity threshold slider
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
        
        # Recursive scan checkbox
        self.recursive_scan_checkbox = QCheckBox("Scan Subdirectories")
        self.recursive_scan_checkbox.setChecked(True)
        search_layout.addRow("", self.recursive_scan_checkbox)
        
        main_layout.addWidget(search_group)
        
        # Create auto-selection preferences group
        auto_select_group = QGroupBox("Auto-Selection Preferences")
        auto_select_layout = QVBoxLayout(auto_select_group)
        
        # Enable auto-selection
        self.enable_auto_select = QCheckBox("Enable automatic selection of best matches")
        self.enable_auto_select.setChecked(True)
        self.enable_auto_select.setToolTip("Automatically select the best match for each entry in auto search")
        auto_select_layout.addWidget(self.enable_auto_select)
        
        # Minimum match score for auto-selection
        min_score_layout = QHBoxLayout()
        min_score_layout.addWidget(QLabel("Minimum score for auto-selection:"))
        
        self.min_score_slider = QSlider(Qt.Horizontal)
        self.min_score_slider.setRange(0, 100)
        self.min_score_slider.setValue(80)
        self.min_score_slider.setTickPosition(QSlider.TicksBelow)
        self.min_score_slider.setTickInterval(10)
        min_score_layout.addWidget(self.min_score_slider)
        
        self.min_score_label = QLabel("80%")
        self.min_score_slider.valueChanged.connect(self._update_min_score_label)
        min_score_layout.addWidget(self.min_score_label)
        
        auto_select_layout.addLayout(min_score_layout)
        
        # Format preferences
        format_pref_layout = QVBoxLayout()
        format_pref_layout.addWidget(QLabel("Format Preferences (higher = more preferred):"))
        
        # Create format preference list
        self.format_preference_list = QListWidget()
        self.format_preference_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.format_preference_list.setToolTip("Drag and drop to reorder preferences. Top = most preferred.")
        
        # Add format items (will be populated in load_settings)
        default_formats = ["flac", "mp3", "m4a", "aac", "wav"]
        for fmt in default_formats:
            item = QListWidgetItem(fmt.upper())
            item.setData(Qt.UserRole, fmt)
            self.format_preference_list.addItem(item)
        
        format_pref_layout.addWidget(self.format_preference_list)
        
        # Format preference buttons
        format_buttons_layout = QHBoxLayout()
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.clicked.connect(self.move_format_up)
        format_buttons_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.clicked.connect(self.move_format_down)
        format_buttons_layout.addWidget(self.move_down_button)
        
        format_buttons_layout.addStretch()
        format_pref_layout.addLayout(format_buttons_layout)
        
        auto_select_layout.addLayout(format_pref_layout)
        
        # Quality preferences
        quality_layout = QFormLayout()
        
        # Prefer higher bitrate
        self.prefer_higher_bitrate = QCheckBox("Prefer higher bitrate")
        self.prefer_higher_bitrate.setChecked(True)
        self.prefer_higher_bitrate.setToolTip("When match scores are similar, prefer files with higher bitrate")
        quality_layout.addRow("Quality:", self.prefer_higher_bitrate)
        
        # Score difference tolerance for quality preferences
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("Score tolerance for quality preferences:"))
        
        self.score_tolerance_spin = QSpinBox()
        self.score_tolerance_spin.setRange(0, 20)
        self.score_tolerance_spin.setValue(5)
        self.score_tolerance_spin.setSuffix("%")
        self.score_tolerance_spin.setToolTip("If quality preference has score within this range of best match, prefer quality")
        tolerance_layout.addWidget(self.score_tolerance_spin)
        
        quality_layout.addRow(tolerance_layout)
        
        auto_select_layout.addLayout(quality_layout)
        main_layout.addWidget(auto_select_group)
        
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
        self.format_preference_list.itemSelectionChanged.connect(self._update_format_buttons)

    def _update_format_buttons(self):
        """Update format preference button states."""
        current_row = self.format_preference_list.currentRow()
        total_rows = self.format_preference_list.count()
        
        self.move_up_button.setEnabled(current_row > 0)
        self.move_down_button.setEnabled(current_row >= 0 and current_row < total_rows - 1)

    def move_format_up(self):
        """Move selected format up in preference list."""
        current_row = self.format_preference_list.currentRow()
        if current_row > 0:
            item = self.format_preference_list.takeItem(current_row)
            self.format_preference_list.insertItem(current_row - 1, item)
            self.format_preference_list.setCurrentRow(current_row - 1)

    def move_format_down(self):
        """Move selected format down in preference list."""
        current_row = self.format_preference_list.currentRow()
        if current_row >= 0 and current_row < self.format_preference_list.count() - 1:
            item = self.format_preference_list.takeItem(current_row)
            self.format_preference_list.insertItem(current_row + 1, item)
            self.format_preference_list.setCurrentRow(current_row + 1)

    def get_format_preferences(self):
        """Get current format preferences as ordered list."""
        preferences = []
        for i in range(self.format_preference_list.count()):
            item = self.format_preference_list.item(i)
            preferences.append(item.data(Qt.UserRole))
        return preferences

    def set_format_preferences(self, preferences):
        """Set format preferences from ordered list."""
        self.format_preference_list.clear()
        for fmt in preferences:
            item = QListWidgetItem(fmt.upper())
            item.setData(Qt.UserRole, fmt)
            self.format_preference_list.addItem(item)

    def browse_export_directory(self):
        """Browse for default export directory using app root as default."""
        # Get app root directory as default
        default_dir = self.get_app_root_directory()
        
        # If there's already a directory set, use that as the starting point
        current_dir = self.export_dir_input.text().strip()
        if current_dir and os.path.exists(current_dir):
            default_dir = current_dir
        
        logger.info(f"Using default directory for export browse: {default_dir}")
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Export Directory",
            default_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.export_dir_input.setText(directory)
            logger.info(f"Selected export directory: {directory}")
    
    def _update_threshold_label(self, value):
        """Update threshold label when slider value changes."""
        self.threshold_label.setText(f"{value}%")
        self.music_indexer.set_similarity_threshold(value)

    def _update_min_score_label(self, value):
        """Update minimum score label when slider value changes."""
        self.min_score_label.setText(f"{value}%")
    
    def _update_dir_buttons(self):
        """Update directory button states based on selection."""
        self.remove_dir_button.setEnabled(self.directory_list.currentItem() is not None)
    
    def update_directory_list(self):
        """Update the directory list widget."""
        self.directory_list.clear()
        directories = self.music_indexer.get_music_directories()
        for directory in directories:
            self.directory_list.addItem(directory)
        self._update_dir_buttons()
    
    def add_directory(self):
        """Add a music directory using app root as default."""
        # Get app root directory as default
        default_dir = self.get_app_root_directory()
        
        logger.info(f"Using default directory for add directory browse: {default_dir}")
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Music Directory",
            default_dir,
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
                logger.info(f"Added music directory: {directory}")
            else:
                QMessageBox.warning(
                    self,
                    "Failed to Add Directory",
                    f"Failed to add directory: {directory}"
                )
                logger.warning(f"Failed to add music directory: {directory}")
    
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
                logger.info(f"Removed music directory: {directory}")
            else:
                QMessageBox.warning(
                    self,
                    "Failed to Remove Directory",
                    f"Failed to remove directory: {directory}"
                )
                logger.warning(f"Failed to remove music directory: {directory}")
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load existing settings
        threshold = settings.value("search/threshold", 75, type=int)
        self.threshold_slider.setValue(threshold)
        
        recursive = settings.value("indexing/recursive", True, type=bool)
        self.recursive_scan_checkbox.setChecked(recursive)
        
        supported_formats = self.music_indexer.config_manager.get_supported_formats()
        for fmt, checkbox in self.format_checkboxes.items():
            checkbox.setChecked(fmt in supported_formats)
        
        export_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        self.export_dir_input.setText(export_dir)
        
        theme = settings.value("appearance/theme", "System Default")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Load auto-selection settings
        self.enable_auto_select.setChecked(settings.value("auto_select/enabled", True, type=bool))
        
        min_score = settings.value("auto_select/min_score", 80, type=int)
        self.min_score_slider.setValue(min_score)
        
        # Load format preferences
        format_prefs = settings.value("auto_select/format_preferences", ["flac", "mp3", "m4a", "aac", "wav"])
        if isinstance(format_prefs, str):
            format_prefs = [format_prefs]  # Handle single item case
        self.set_format_preferences(format_prefs)
        
        self.prefer_higher_bitrate.setChecked(settings.value("auto_select/prefer_higher_bitrate", True, type=bool))
        
        tolerance = settings.value("auto_select/score_tolerance", 5, type=int)
        self.score_tolerance_spin.setValue(tolerance)
        
        # Load ignore suffixes
        ignore_suffixes = self.music_indexer.config_manager.get("search", "ignore_suffixes", 
                                                              ["justify", "sob", "nrg", "dps", "trt", "pms"])
        self.ignore_suffixes_input.setText(", ".join(ignore_suffixes))
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save existing settings
        threshold = self.threshold_slider.value()
        settings.setValue("search/threshold", threshold)
        self.music_indexer.set_similarity_threshold(threshold)
        
        recursive = self.recursive_scan_checkbox.isChecked()
        settings.setValue("indexing/recursive", recursive)
        
        supported_formats = []
        for fmt, checkbox in self.format_checkboxes.items():
            if checkbox.isChecked():
                supported_formats.append(fmt)
        
        self.music_indexer.config_manager.set("indexing", "supported_formats", supported_formats)
        
        export_dir = self.export_dir_input.text()
        self.music_indexer.config_manager.set("paths", "default_export_directory", export_dir)
        
        theme = self.theme_combo.currentText()
        settings.setValue("appearance/theme", theme)
        self._apply_theme(theme)
        
        # Save auto-selection settings
        settings.setValue("auto_select/enabled", self.enable_auto_select.isChecked())
        settings.setValue("auto_select/min_score", self.min_score_slider.value())
        settings.setValue("auto_select/format_preferences", self.get_format_preferences())
        settings.setValue("auto_select/prefer_higher_bitrate", self.prefer_higher_bitrate.isChecked())
        settings.setValue("auto_select/score_tolerance", self.score_tolerance_spin.value())
        
        # Save ignore suffixes
        suffixes_text = self.ignore_suffixes_input.text().strip()
        if suffixes_text:
            suffixes_list = [s.strip() for s in suffixes_text.split(',') if s.strip()]
            self.music_indexer.config_manager.set("search", "ignore_suffixes", suffixes_list)
        else:
            self.music_indexer.config_manager.set("search", "ignore_suffixes", [])        
        
        QMessageBox.information(
            self,
            "Settings Saved",
            "Settings saved successfully. Auto-selection preferences will be applied to future searches."
        )
    
    def _apply_theme(self, theme):
        """Apply the selected theme."""
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication.instance()
        
        if theme == "Dark":
            # Apply dark theme stylesheet
            dark_style = """
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #555555;
            }
            QGroupBox {
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QComboBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 2px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ffffff;
            }
            QSlider::groove:horizontal {
                background-color: #404040;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #ffffff;
                width: 12px;
                border-radius: 6px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #404040;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            """
            app.setStyleSheet(dark_style)
            logger.info("Applied dark theme")
            
        elif theme == "Light":
            # Apply light theme stylesheet
            light_style = """
            QMainWindow, QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #000000;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #cccccc;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QGroupBox {
                color: #000000;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 2px;
            }
            QSlider::groove:horizontal {
                background-color: #e0e0e0;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #0078d4;
                width: 12px;
                border-radius: 6px;
            }
            QCheckBox {
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QMenuBar {
                background-color: #f0f0f0;
                color: #000000;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #000000;
            }
            """
            app.setStyleSheet(light_style)
            logger.info("Applied light theme")
            
        else:  # System Default
            app.setStyleSheet("")
            logger.info("Applied system default theme")
    
    def closeEvent(self, event):
        """Handle panel close event."""
        super().closeEvent(event)