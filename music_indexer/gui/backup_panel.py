"""
Dedicated Backup & Restore tab panel for the music indexer application.
"""
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QFormLayout, QLineEdit, QCheckBox,
    QFileDialog, QMessageBox, QProgressDialog, QFrame,
    QTextEdit, QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont

from ..utils.logger import get_logger
from ..utils.backup_manager import BackupManager

logger = get_logger()


class BackupPanel(QWidget):
    """Dedicated backup and restore panel for the Music Indexer application."""
    
    def __init__(self, music_indexer):
        """Initialize the backup panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        self.backup_manager = BackupManager(music_indexer.config_manager)
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Backup panel initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create main layout with scroll area for small screens
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Main content widget
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        
        # Title
        title_label = QLabel("Database Backup & Restore")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Description
        description_label = QLabel(
            "Backup your indexed music database and configuration to protect against data loss. "
            "Restore from backups to migrate between computers or recover from issues."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin: 10px 0;")
        main_layout.addWidget(description_label)
        
        # Current database info section
        info_group = QGroupBox("Current Database Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")
        info_layout.addWidget(self.info_text)
        
        refresh_info_btn = QPushButton("Refresh Info")
        refresh_info_btn.clicked.connect(self.update_database_info)
        info_layout.addWidget(refresh_info_btn)
        
        main_layout.addWidget(info_group)
        
        # Create splitter for backup and restore sections
        splitter = QSplitter(Qt.Horizontal)
        
        # Backup section
        backup_section = self.create_backup_section()
        splitter.addWidget(backup_section)
        
        # Restore section  
        restore_section = self.create_restore_section()
        splitter.addWidget(restore_section)
        
        # Set equal sizes
        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter)
        
        # Recent backups section
        recent_group = self.create_recent_backups_section()
        main_layout.addWidget(recent_group)
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Main panel layout
        panel_layout = QVBoxLayout(self)
        panel_layout.addWidget(scroll_area)
        
        # Initial data update
        self.update_database_info()
    
    def create_backup_section(self):
        """Create the backup section."""
        backup_group = QGroupBox("Create Backup")
        backup_layout = QVBoxLayout(backup_group)
        
        # Format selection
        format_layout = QFormLayout()
        
        self.backup_format_combo = QComboBox()
        self.backup_format_combo.addItems(["zip", "tar.gz", "tar", "7z"])
        self.backup_format_combo.setCurrentText("zip")
        self.backup_format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addRow("Archive Format:", self.backup_format_combo)
        
        # Include config checkbox
        self.include_config_checkbox = QCheckBox("Include configuration file (config.ini)")
        self.include_config_checkbox.setChecked(True)
        self.include_config_checkbox.setToolTip("Include your settings and preferences in the backup")
        format_layout.addRow("", self.include_config_checkbox)
        
        backup_layout.addLayout(format_layout)
        
        # Backup location
        location_layout = QVBoxLayout()
        location_layout.addWidget(QLabel("Backup Location:"))
        
        path_layout = QHBoxLayout()
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setPlaceholderText("Choose where to save the backup...")
        path_layout.addWidget(self.backup_path_input)
        
        self.browse_backup_button = QPushButton("Browse")
        self.browse_backup_button.clicked.connect(self.browse_backup_location)
        path_layout.addWidget(self.browse_backup_button)
        
        location_layout.addLayout(path_layout)
        backup_layout.addLayout(location_layout)
        
        # Auto-generate filename button
        auto_name_btn = QPushButton("Auto-Generate Filename")
        auto_name_btn.clicked.connect(self.auto_generate_backup_name)
        backup_layout.addWidget(auto_name_btn)
        
        # Create backup button
        self.create_backup_button = QPushButton("Create Backup")
        self.create_backup_button.clicked.connect(self.create_backup)
        self.create_backup_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        backup_layout.addWidget(self.create_backup_button)
        
        backup_layout.addStretch()
        return backup_group
    
    def create_restore_section(self):
        """Create the restore section."""
        restore_group = QGroupBox("Restore from Backup")
        restore_layout = QVBoxLayout(restore_group)
        
        # Backup file selection
        file_layout = QVBoxLayout()
        file_layout.addWidget(QLabel("Select Backup File:"))
        
        path_layout = QHBoxLayout()
        self.restore_path_input = QLineEdit()
        self.restore_path_input.setPlaceholderText("Choose backup file to restore...")
        self.restore_path_input.textChanged.connect(self.on_restore_file_changed)
        path_layout.addWidget(self.restore_path_input)
        
        self.browse_restore_button = QPushButton("Browse")
        self.browse_restore_button.clicked.connect(self.browse_restore_file)
        path_layout.addWidget(self.browse_restore_button)
        
        file_layout.addLayout(path_layout)
        restore_layout.addLayout(file_layout)
        
        # Restore options
        options_layout = QFormLayout()
        
        self.restore_config_checkbox = QCheckBox("Restore configuration file")
        self.restore_config_checkbox.setChecked(True)
        self.restore_config_checkbox.setToolTip("Restore your settings and preferences")
        options_layout.addRow("", self.restore_config_checkbox)
        
        self.backup_existing_checkbox = QCheckBox("Backup existing files before restore")
        self.backup_existing_checkbox.setChecked(True)
        self.backup_existing_checkbox.setToolTip("Create safety backup of current files")
        options_layout.addRow("", self.backup_existing_checkbox)
        
        restore_layout.addLayout(options_layout)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        self.verify_backup_button = QPushButton("Verify Backup Integrity")
        self.verify_backup_button.clicked.connect(self.verify_backup)
        self.verify_backup_button.setEnabled(False)
        button_layout.addWidget(self.verify_backup_button)
        
        self.restore_backup_button = QPushButton("Restore Backup")
        self.restore_backup_button.clicked.connect(self.restore_backup)
        self.restore_backup_button.setEnabled(False)
        self.restore_backup_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.restore_backup_button)
        
        restore_layout.addLayout(button_layout)
        restore_layout.addStretch()
        return restore_group
    
    def create_recent_backups_section(self):
        """Create section showing recent backup files."""
        recent_group = QGroupBox("Quick Access")
        recent_layout = QHBoxLayout(recent_group)
        
        # Quick backup button
        quick_backup_btn = QPushButton("Quick Backup (Default Settings)")
        quick_backup_btn.clicked.connect(self.quick_backup)
        quick_backup_btn.setToolTip("Create backup with default settings to default location")
        recent_layout.addWidget(quick_backup_btn)
        
        # Open backup folder button
        open_folder_btn = QPushButton("Open Backup Folder")
        open_folder_btn.clicked.connect(self.open_backup_folder)
        open_folder_btn.setToolTip("Open the default backup directory")
        recent_layout.addWidget(open_folder_btn)
        
        recent_layout.addStretch()
        
        return recent_group
    
    def update_database_info(self):
        """Update the database information display."""
        try:
            info = self.backup_manager.get_backup_info()
            
            info_text = ""
            if info['database_exists']:
                db_size_mb = info['database_size'] / (1024 * 1024)
                info_text += f"📊 Database Status: Active\n"
                info_text += f"📁 File Count: {info['total_files']:,} indexed music files\n"
                info_text += f"💾 Database Size: {db_size_mb:.1f} MB\n"
                info_text += f"📍 Location: {info['database_file']}\n"
            else:
                info_text += "❌ Database Status: Not found\n"
                info_text += "ℹ️  No database file exists. Index some music files first.\n"
            
            if info['config_exists']:
                config_size_kb = info['config_size'] / 1024
                info_text += f"⚙️ Configuration: {config_size_kb:.1f} KB"
            else:
                info_text += "⚙️ Configuration: Default settings (no config file)"
            
            self.info_text.setPlainText(info_text)
            
            # Enable/disable backup button
            self.create_backup_button.setEnabled(info['database_exists'])
            
            if not info['database_exists']:
                self.create_backup_button.setToolTip("No database to backup. Index some music files first.")
            else:
                self.create_backup_button.setToolTip("Create backup of your indexed music database")
                
        except Exception as e:
            logger.error(f"Error updating database info: {str(e)}")
            self.info_text.setPlainText("❌ Error retrieving database information")
    
    def on_format_changed(self):
        """Handle format change to update file extension."""
        current_path = self.backup_path_input.text()
        if current_path:
            # Update extension if path already exists
            base_path = os.path.splitext(current_path)[0]
            new_extension = self.backup_format_combo.currentText()
            new_path = f"{base_path}.{new_extension}"
            self.backup_path_input.setText(new_path)
    
    def on_restore_file_changed(self):
        """Handle restore file path change."""
        has_file = bool(self.restore_path_input.text().strip())
        self.verify_backup_button.setEnabled(has_file)
        self.restore_backup_button.setEnabled(has_file)
    
    def auto_generate_backup_name(self):
        """Auto-generate a backup filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        format_type = self.backup_format_combo.currentText()
        filename = f"music_indexer_backup_{timestamp}.{format_type}"
        
        # Get default directory
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
        
        full_path = os.path.join(default_dir, filename)
        self.backup_path_input.setText(full_path)
    
    def browse_backup_location(self):
        """Browse for backup save location."""
        format_type = self.backup_format_combo.currentText()
        default_name = f"music_indexer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        
        # Get default directory
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
        
        default_path = os.path.join(default_dir, default_name)
        
        # File dialog filter based on format
        filter_map = {
            "zip": "ZIP Archives (*.zip)",
            "7z": "7z Archives (*.7z)",
            "tar": "TAR Archives (*.tar)",
            "tar.gz": "Compressed TAR Archives (*.tar.gz)"
        }
        
        file_filter = filter_map.get(format_type, "All Files (*.*)")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup As",
            default_path,
            f"{file_filter};;All Files (*.*)"
        )
        
        if file_path:
            self.backup_path_input.setText(file_path)
    
    def browse_restore_file(self):
        """Browse for backup file to restore."""
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            default_dir,
            "Backup Files (*.zip *.tar *.tar.gz *.7z);;ZIP Archives (*.zip);;TAR Archives (*.tar);;Compressed TAR (*.tar.gz);;7z Archives (*.7z);;All Files (*.*)"
        )
        
        if file_path:
            self.restore_path_input.setText(file_path)
    
    def quick_backup(self):
        """Create a quick backup with default settings."""
        # Auto-generate filename
        self.auto_generate_backup_name()
        
        # Create backup
        self.create_backup()
    
    def open_backup_folder(self):
        """Open the default backup directory."""
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
        
        try:
            import subprocess
            import sys
            
            if sys.platform == "win32":
                os.startfile(default_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", default_dir])
            else:
                subprocess.run(["xdg-open", default_dir])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")
    
    def create_backup(self):
        """Create a backup of the database and configuration."""
        backup_path = self.backup_path_input.text().strip()
        
        if not backup_path:
            QMessageBox.warning(
                self,
                "Missing Backup Path",
                "Please specify where to save the backup file."
            )
            return
        
        format_type = self.backup_format_combo.currentText()
        include_config = self.include_config_checkbox.isChecked()
        
        # Show progress dialog
        progress = QProgressDialog("Creating backup...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Creating Backup")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        try:
            success, message, backup_file = self.backup_manager.create_backup(
                backup_path, format_type, include_config
            )
            
            progress.close()
            
            if success:
                # Update database info
                self.update_database_info()
                
                # Show success with file details
                if backup_file and os.path.exists(backup_file):
                    backup_size = os.path.getsize(backup_file)
                    backup_size_mb = backup_size / (1024 * 1024)
                    
                    QMessageBox.information(
                        self,
                        "Backup Created Successfully",
                        f"✅ Backup created successfully!\n\n"
                        f"📁 File: {os.path.basename(backup_file)}\n"
                        f"💾 Size: {backup_size_mb:.1f} MB\n"
                        f"📦 Format: {format_type.upper()}\n"
                        f"⚙️ Includes config: {'Yes' if include_config else 'No'}\n\n"
                        f"📍 Location: {backup_file}"
                    )
                else:
                    QMessageBox.information(self, "Backup Created", message)
            else:
                QMessageBox.warning(self, "Backup Failed", f"❌ {message}")
        
        except Exception as e:
            progress.close()
            logger.error(f"Error creating backup: {str(e)}")
            QMessageBox.critical(
                self,
                "Backup Error",
                f"An unexpected error occurred while creating the backup:\n{str(e)}"
            )
    
    def verify_backup(self):
        """Verify the integrity of a backup file."""
        backup_file = self.restore_path_input.text().strip()
        
        if not backup_file:
            QMessageBox.warning(
                self,
                "No Backup Selected",
                "Please select a backup file to verify."
            )
            return
        
        # Show progress dialog
        progress = QProgressDialog("Verifying backup...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Verifying Backup")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        try:
            success, message = self.backup_manager.verify_backup(backup_file)
            
            # Also get contents for detailed info
            contents_success, contents, metadata = self.backup_manager.list_backup_contents(backup_file)
            
            progress.close()
            
            if success:
                # Show detailed verification results
                info_text = f"✅ {message}"
                
                if contents_success and contents:
                    info_text += f"\n\n📋 Backup contents ({len(contents)} files):\n"
                    for item in contents:
                        size_mb = item.get('size', 0) / (1024 * 1024)
                        info_text += f"• {item['name']}: {size_mb:.1f} MB\n"
                
                if metadata:
                    created_at = metadata.get('created_at', 'Unknown')
                    info_text += f"\n📅 Created: {created_at}"
                    
                    backup_info = metadata.get('backup_info', {})
                    if backup_info.get('total_files'):
                        info_text += f"\n📊 Original records: {backup_info['total_files']:,}"
                
                QMessageBox.information(
                    self,
                    "Backup Verification Successful",
                    info_text
                )
            else:
                QMessageBox.warning(
                    self,
                    "Backup Verification Failed",
                    f"❌ Backup verification failed:\n{message}"
                )
        
        except Exception as e:
            progress.close()
            logger.error(f"Error verifying backup: {str(e)}")
            QMessageBox.critical(
                self,
                "Verification Error",
                f"An unexpected error occurred while verifying the backup:\n{str(e)}"
            )
    
    def restore_backup(self):
        """Restore database and configuration from backup."""
        backup_file = self.restore_path_input.text().strip()
        
        if not backup_file:
            QMessageBox.warning(
                self,
                "No Backup Selected",
                "Please select a backup file to restore."
            )
            return
        
        restore_config = self.restore_config_checkbox.isChecked()
        backup_existing = self.backup_existing_checkbox.isChecked()
        
        # Confirmation dialog
        confirm_text = f"⚠️ Are you sure you want to restore from this backup?\n\n"
        confirm_text += f"📁 Backup file: {os.path.basename(backup_file)}\n"
        confirm_text += f"⚙️ Restore configuration: {'Yes' if restore_config else 'No'}\n"
        confirm_text += f"🛡️ Backup existing files: {'Yes' if backup_existing else 'No'}\n\n"
        confirm_text += "🔄 This will replace your current database"
        if restore_config:
            confirm_text += " and configuration"
        confirm_text += "."
        
        reply = QMessageBox.question(
            self,
            "Confirm Restore Operation",
            confirm_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Show progress dialog
        progress = QProgressDialog("Restoring backup...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Restoring Backup")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        try:
            success, message = self.backup_manager.restore_backup(
                backup_file, restore_config, backup_existing
            )
            
            progress.close()
            
            if success:
                # Update database info display
                self.update_database_info()
                
                QMessageBox.information(
                    self,
                    "Restore Complete",
                    f"✅ Backup restored successfully!\n\n{message}\n\n"
                    "🔄 The application may need to be restarted for all changes to take effect."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Restore Failed",
                    f"❌ Backup restore failed:\n{message}"
                )
        
        except Exception as e:
            progress.close()
            logger.error(f"Error restoring backup: {str(e)}")
            QMessageBox.critical(
                self,
                "Restore Error",
                f"An unexpected error occurred while restoring the backup:\n{str(e)}"
            )
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load backup preferences
        backup_format = settings.value("backup/format", "zip")
        index = self.backup_format_combo.findText(backup_format)
        if index >= 0:
            self.backup_format_combo.setCurrentIndex(index)
        
        include_config = settings.value("backup/include_config", True, type=bool)
        self.include_config_checkbox.setChecked(include_config)
        
        restore_config = settings.value("backup/restore_config", True, type=bool)
        self.restore_config_checkbox.setChecked(restore_config)
        
        backup_existing = settings.value("backup/backup_existing", True, type=bool)
        self.backup_existing_checkbox.setChecked(backup_existing)
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save backup preferences
        settings.setValue("backup/format", self.backup_format_combo.currentText())
        settings.setValue("backup/include_config", self.include_config_checkbox.isChecked())
        settings.setValue("backup/restore_config", self.restore_config_checkbox.isChecked())
        settings.setValue("backup/backup_existing", self.backup_existing_checkbox.isChecked())
    
    def closeEvent(self, event):
        """Handle panel close event."""
        self.save_settings()
        super().closeEvent(event)