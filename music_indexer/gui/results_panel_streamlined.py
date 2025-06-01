"""
Enhanced results panel GUI with streamlined view, resizable columns, sorting, and save/load functionality for the music indexer application.
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QProgressDialog, QCheckBox,
    QMenu, QStyle, QGroupBox, QButtonGroup, QComboBox,
    QFrame, QSplitter
)
from PyQt5.QtCore import Qt, QSettings, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QIcon, QBrush, QFont

from ..utils.logger import get_logger

logger = get_logger()


class MatchDropdown(QComboBox):
    """Custom dropdown widget for showing multiple matches for a single entry."""
    
    matchChanged = pyqtSignal(dict)  # Signal emitted when match selection changes
    
    def __init__(self, matches, parent=None):
        super().__init__(parent)
        self.matches = matches
        self.setMinimumWidth(200)
        self.setup_matches()
        self.currentIndexChanged.connect(self.on_selection_changed)
    
    def setup_matches(self):
        """Populate the dropdown with matches."""
        self.clear()
        
        if not self.matches:
            self.addItem("No matches found")
            self.setEnabled(False)
            return
        
        # Add matches to dropdown
        for i, match in enumerate(self.matches):
            filename = match.get('filename', 'Unknown')
            score = match.get('combined_score', 0)
            format_type = match.get('format', '').upper()
            bitrate = match.get('bitrate', 0)
            
            # Create display text
            display_text = f"{filename} ({score:.1f}% - {format_type} {bitrate}kbps)"
            self.addItem(display_text)
            
            # Store the match data
            self.setItemData(i, match, Qt.UserRole)
    
    def on_selection_changed(self, index):
        """Handle selection change."""
        if index >= 0:
            match_data = self.itemData(index, Qt.UserRole)
            if match_data:
                self.matchChanged.emit(match_data)
    
    def get_selected_match(self):
        """Get the currently selected match."""
        current_index = self.currentIndex()
        if current_index >= 0:
            return self.itemData(current_index, Qt.UserRole)
        return None


class StreamlinedResultsPanel(QWidget):
    """Streamlined results panel with dropdown matches, save/load functionality, and enhanced features."""
    
    def __init__(self, music_indexer):
        """Initialize the streamlined results panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        self.current_results = []
        self.grouped_results = {}
        self.auto_selected_files = set()  # Track auto-selected files
        self.match_dropdowns = []  # Store dropdown references as list
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Streamlined results panel with save/load functionality initialized")
    
    def get_app_root_directory(self):
        """
        Get the app root directory (where main.py is located).
        
        Returns:
            str: Path to app root directory
        """
        # Get the directory where main.py is located
        # Since we're in music_indexer/gui/results_panel_streamlined.py, we need to go up 2 levels
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
        
        # Create bulk selection controls
        selection_group = QGroupBox("Bulk Selection")
        selection_layout = QHBoxLayout(selection_group)
        
        self.auto_select_button = QPushButton("Auto-Select Best Matches")
        self.auto_select_button.clicked.connect(self.auto_select_best_matches)
        self.auto_select_button.setToolTip("Automatically select the best match for each entry based on preferences")
        selection_layout.addWidget(self.auto_select_button)
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_matches)
        selection_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all_matches)
        selection_layout.addWidget(self.deselect_all_button)
        
        selection_layout.addStretch()
        
        # Selection summary
        self.selection_summary_label = QLabel("No files selected")
        selection_layout.addWidget(self.selection_summary_label)
        
        main_layout.addWidget(selection_group)
        
        # Create results tree with streamlined view
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(8)
        self.results_tree.setHeaderLabels([
            "☐", "Playlist Entry", "Original Search", "Best Match", "Format", "Duration", "Bitrate", "Score"
        ])
        
        # Set tree properties
        self.results_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.results_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.results_tree.itemChanged.connect(self.on_item_changed)
        
        # Enable sorting
        self.results_tree.setSortingEnabled(True)
        self.results_tree.sortByColumn(7, Qt.DescendingOrder)  # Sort by score descending
        
        # Set column properties for better usability
        header = self.results_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox column
        header.setSectionResizeMode(1, QHeaderView.Interactive)       # Playlist Entry
        header.setSectionResizeMode(2, QHeaderView.Interactive)       # Original Search
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Best Match (main column)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Format
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Bitrate
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Score
        
        # Set minimum column widths
        header.setMinimumSectionSize(80)
        self.results_tree.setColumnWidth(1, 250)  # Playlist Entry
        self.results_tree.setColumnWidth(2, 200)  # Original Search
        self.results_tree.setColumnWidth(3, 300)  # Best Match
        
        # Make header clickable for sorting
        header.sectionClicked.connect(self.on_header_clicked)
        
        # Add tree to layout
        main_layout.addWidget(self.results_tree)
        
        # Create status label
        self.status_label = QLabel("No results to display")
        main_layout.addWidget(self.status_label)
        
        # Create enhanced button layout
        button_layout = QHBoxLayout()
        
        # Copy selected files button (enhanced)
        self.copy_selected_button = QPushButton("Copy Selected Files")
        self.copy_selected_button.clicked.connect(self.copy_selected_files)
        self.copy_selected_button.setEnabled(False)
        self.copy_selected_button.setStyleSheet("font-weight: bold;")
        button_layout.addWidget(self.copy_selected_button)
        
        # Add "Show in Folder" button
        self.show_folder_button = QPushButton("Show in Folder")
        self.show_folder_button.clicked.connect(self.show_in_folder)
        self.show_folder_button.setEnabled(False)
        button_layout.addWidget(self.show_folder_button)
        
        # Add "Save Results" button
        self.save_results_button = QPushButton("Save Results")
        self.save_results_button.clicked.connect(self.save_auto_search_results)
        self.save_results_button.setEnabled(False)
        self.save_results_button.setToolTip("Save current auto search results to reload later")
        button_layout.addWidget(self.save_results_button)
        
        # Add "Load Results" button  
        self.load_results_button = QPushButton("Load Results")
        self.load_results_button.clicked.connect(self.load_auto_search_results)
        self.load_results_button.setToolTip("Load previously saved auto search results")
        button_layout.addWidget(self.load_results_button)
        
        # Add "Export Results" button
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        # Add "Export Missing Tracks" button
        self.export_missing_button = QPushButton("Export Missing Tracks")
        self.export_missing_button.clicked.connect(self.export_missing_tracks)
        self.export_missing_button.setEnabled(False)
        self.export_missing_button.setToolTip("Export tracks with no matches to a text file for follow-up searching")
        button_layout.addWidget(self.export_missing_button)
        
        # Add "Clear Results" button
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setEnabled(False)
        button_layout.addWidget(self.clear_button)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Connect signals
        self.results_tree.itemSelectionChanged.connect(self.update_button_states)
    
    def save_auto_search_results(self):
        """Save current auto search results to a file."""
        if not self.grouped_results:
            QMessageBox.information(
                self,
                "No Results to Save",
                "No auto search results available to save."
            )
            return
        
        # Get app root directory as default
        default_dir = self.get_app_root_directory()
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        algorithm = "enhanced" if hasattr(self, 'is_enhanced_search') and getattr(self, 'is_enhanced_search', False) else "standard"
        default_filename = f"autosearch_results_{algorithm}_{timestamp}.json"
        default_path = os.path.join(default_dir, default_filename)
        
        # Get save path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Auto Search Results",
            default_path,
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Prepare data for saving
            save_data = {
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'app_version': '0.1.0',  # You can get this from config
                    'algorithm_used': algorithm,
                    'total_entries': len(self.grouped_results),
                    'entries_with_matches': sum(1 for r in self.grouped_results.values() if r.get('matches')),
                    'total_matches': sum(len(r.get('matches', [])) for r in self.grouped_results.values()),
                    'selected_files': list(self.auto_selected_files),
                    'selected_count': len(self.auto_selected_files)
                },
                'grouped_results': self.grouped_results,
                'auto_selected_files': list(self.auto_selected_files),
                'search_settings': {
                    'similarity_threshold': getattr(getattr(self.music_indexer, 'string_matcher', None), 'threshold', 75),
                    'is_auto_search': getattr(self, 'is_auto_search', True),
                    'algorithm': algorithm
                }
            }
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # Show success message
            file_size = os.path.getsize(file_path)
            file_size_kb = file_size / 1024
            
            QMessageBox.information(
                self,
                "Results Saved Successfully",
                f"✅ Auto search results saved successfully!\n\n"
                f"📁 File: {os.path.basename(file_path)}\n"
                f"💾 Size: {file_size_kb:.1f} KB\n"
                f"📊 Entries: {save_data['metadata']['total_entries']}\n"
                f"🎯 Matches: {save_data['metadata']['total_matches']}\n"
                f"✅ Selected: {save_data['metadata']['selected_count']}\n\n"
                f"📍 Location: {file_path}"
            )
            
            logger.info(f"Saved auto search results to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving auto search results: {str(e)}")
            QMessageBox.warning(
                self,
                "Save Failed",
                f"Failed to save auto search results:\n{str(e)}"
            )
    
    def load_auto_search_results(self):
        """Load auto search results from a file."""
        # Get app root directory as default
        default_dir = self.get_app_root_directory()
        
        # Get file path from user
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Auto Search Results",
            default_dir,
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The selected file does not exist:\n{file_path}"
            )
            return
        
        try:
            # Load data from file
            with open(file_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Validate file format
            if 'grouped_results' not in save_data or 'metadata' not in save_data:
                QMessageBox.warning(
                    self,
                    "Invalid File Format",
                    "The selected file does not appear to be a valid auto search results file."
                )
                return
            
            # Extract data
            metadata = save_data['metadata']
            grouped_results = save_data['grouped_results']
            auto_selected_files = set(save_data.get('auto_selected_files', []))
            search_settings = save_data.get('search_settings', {})
            
            # Validate that files still exist
            missing_files = []
            valid_selected_files = set()
            
            for file_path_check in auto_selected_files:
                if os.path.exists(file_path_check):
                    valid_selected_files.add(file_path_check)
                else:
                    missing_files.append(file_path_check)
            
            # Show confirmation dialog with file info
            created_at = metadata.get('created_at', 'Unknown')
            algorithm = metadata.get('algorithm_used', 'Unknown')
            total_entries = metadata.get('total_entries', 0)
            total_matches = metadata.get('total_matches', 0)
            original_selected = metadata.get('selected_count', 0)
            current_valid = len(valid_selected_files)
            
            confirm_text = f"📁 Load Auto Search Results\n\n"
            confirm_text += f"📅 Created: {created_at}\n"
            confirm_text += f"🔧 Algorithm: {algorithm.title()}\n"
            confirm_text += f"📊 Entries: {total_entries}\n"
            confirm_text += f"🎯 Total matches: {total_matches}\n"
            confirm_text += f"✅ Originally selected: {original_selected}\n"
            confirm_text += f"✅ Currently valid: {current_valid}\n"
            
            if missing_files:
                confirm_text += f"⚠️ Missing files: {len(missing_files)}\n"
            
            confirm_text += f"\nLoad these results?"
            
            reply = QMessageBox.question(
                self,
                "Load Auto Search Results",
                confirm_text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Load the results
            self.grouped_results = grouped_results
            self.auto_selected_files = valid_selected_files
            self.is_auto_search = search_settings.get('is_auto_search', True)
            
            # Check if this was enhanced search
            if algorithm == 'enhanced':
                self.is_enhanced_search = True
            
            # Display the results
            self.display_streamlined_results()
            
            # Show load completion message
            success_text = f"✅ Results loaded successfully!\n\n"
            success_text += f"📊 Loaded {total_entries} entries with {total_matches} matches\n"
            success_text += f"✅ {current_valid} files selected\n"
            
            if missing_files:
                success_text += f"\n⚠️ Note: {len(missing_files)} previously selected files are no longer available"
            
            QMessageBox.information(
                self,
                "Results Loaded Successfully",
                success_text
            )
            
            logger.info(f"Loaded auto search results from: {file_path}")
            logger.info(f"Loaded {total_entries} entries, {current_valid} valid selections")
            
        except json.JSONDecodeError:
            QMessageBox.warning(
                self,
                "Invalid File Format",
                "The selected file is not a valid JSON file or is corrupted."
            )
        except Exception as e:
            logger.error(f"Error loading auto search results: {str(e)}")
            QMessageBox.warning(
                self,
                "Load Failed",
                f"Failed to load auto search results:\n{str(e)}"
            )
    
    def on_header_clicked(self, logical_index):
        """Handle header clicks for sorting."""
        logger.debug(f"Header clicked: column {logical_index}")
        # Additional sorting logic if needed
    
    def on_item_changed(self, item, column):
        """Handle item checkbox changes."""
        if column == 0:  # Checkbox column
            file_path = item.data(0, Qt.UserRole + 1)
            if file_path:
                if item.checkState(0) == Qt.Checked:
                    self.auto_selected_files.add(file_path)
                else:
                    self.auto_selected_files.discard(file_path)
                self.update_selection_summary()
                self.update_button_states()
    
    def on_match_dropdown_changed(self, item, new_match):
        """Handle match dropdown selection changes."""
        if not new_match:
            return
        
        # Update the displayed information in the tree item
        self.update_tree_item_from_match(item, new_match)
        
        # Update file path in user data
        file_path = new_match.get('file_path', '')
        old_file_path = item.data(0, Qt.UserRole + 1)
        
        if old_file_path != file_path:
            # Remove old selection if it was selected
            if old_file_path in self.auto_selected_files:
                self.auto_selected_files.discard(old_file_path)
                # Keep the item checked and update to new file path
                if item.checkState(0) == Qt.Checked:
                    self.auto_selected_files.add(file_path)
            
            # Update stored file path
            item.setData(0, Qt.UserRole + 1, file_path)
            item.setData(0, Qt.UserRole + 2, new_match)  # Store full match data
            
            self.update_selection_summary()
    
    def update_tree_item_from_match(self, item, match):
        """Update tree item display from match data."""
        filename = match.get('filename', 'Unknown')
        format_type = match.get('format', '')
        duration = match.get('duration', 0)
        bitrate = match.get('bitrate', 0)
        score = match.get('combined_score', 0)
        
        # IMPORTANT: Only update the Best Match column and onwards
        # DO NOT update columns 1 (Playlist Entry) and 2 (Original Search)
        # as these should preserve the original search information
        
        item.setText(3, filename)  # Best Match column
        item.setText(4, format_type.upper())  # Format
        
        # Duration
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_text = f"{minutes}:{seconds:02d}"
        item.setText(5, duration_text)
        
        # Bitrate
        item.setText(6, f"{bitrate}")
        
        # Score
        item.setText(7, f"{score:.1f}%")
        
        # Color code match score
        if score >= 90:
            item.setBackground(7, QColor(200, 255, 200))
        elif score >= 80:
            item.setBackground(7, QColor(220, 255, 220))
        elif score >= 70:
            item.setBackground(7, QColor(255, 255, 200))
        else:
            item.setBackground(7, QColor(255, 220, 220))
    
    def create_match_dropdown(self, matches, tree_item):
        """Create a match dropdown widget for a tree item."""
        dropdown = MatchDropdown(matches)
        
        # Store reference to tree item in the dropdown for later lookup
        dropdown.tree_item = tree_item
        dropdown.matchChanged.connect(lambda match: self.on_match_dropdown_changed(tree_item, match))
        
        # Add to our list of dropdowns
        self.match_dropdowns.append(dropdown)
        
        return dropdown
    
    def update_selection_summary(self):
        """Update the selection summary label."""
        selected_count = len(self.auto_selected_files)
        if selected_count == 0:
            self.selection_summary_label.setText("No files selected")
        elif selected_count == 1:
            self.selection_summary_label.setText("1 file selected")
        else:
            self.selection_summary_label.setText(f"{selected_count} files selected")
    
    def auto_select_best_matches(self):
        """Automatically select the best match for each entry based on user preferences."""
        if not self.grouped_results:
            QMessageBox.information(self, "No Results", "No grouped results available for auto-selection.")
            return
        
        # Get auto-selection preferences
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        if not settings.value("auto_select/enabled", True, type=bool):
            QMessageBox.information(self, "Auto-Select Disabled", 
                                  "Auto-selection is disabled. Enable it in Settings to use this feature.")
            return
        
        # Clear existing selections
        self.deselect_all_matches()
        
        auto_selected_count = 0
        
        # Process each item in the tree
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            
            # Check if item has matches
            matches = item.data(0, Qt.UserRole + 3)  # Stored matches list
            if not matches:
                continue
            
            # Auto-select the first (best) match
            best_match = matches[0]
            file_path = best_match.get('file_path', '')
            
            if file_path:
                item.setCheckState(0, Qt.Checked)
                self.auto_selected_files.add(file_path)
                auto_selected_count += 1
                
                # Update dropdown to show selected match
                dropdown_widget = self.results_tree.itemWidget(item, 3)  # Best Match column (now column 3)
                if dropdown_widget and hasattr(dropdown_widget, 'setCurrentIndex'):
                    dropdown_widget.setCurrentIndex(0)
        
        self.update_selection_summary()
        self.update_button_states()
        
        QMessageBox.information(self, "Auto-Selection Complete", 
                              f"Automatically selected {auto_selected_count} best matches.")
    
    def select_all_matches(self):
        """Select all available matches."""
        self.auto_selected_files.clear()
        
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            file_path = item.data(0, Qt.UserRole + 1)
            if file_path:
                item.setCheckState(0, Qt.Checked)
                self.auto_selected_files.add(file_path)
        
        self.update_selection_summary()
        self.update_button_states()
    
    def deselect_all_matches(self):
        """Deselect all matches."""
        self.auto_selected_files.clear()
        
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
        
        self.update_selection_summary()
        self.update_button_states()
    
    def set_results(self, results):
        """Set search results."""
        self.current_results = results
        
        # Clear previous selections
        self.auto_selected_files.clear()
        self.match_dropdowns.clear()
        
        # Check if results are from auto_search (containing 'line' field)
        self.is_auto_search = any(
            isinstance(r, dict) and 'line' in r and 'matches' in r 
            for r in results
        )
        
        if self.is_auto_search:
            self.grouped_results = {}
            # Group results by source line
            for result in results:
                line = result.get('line', '')
                artist = result.get('artist', '')
                title = result.get('title', '')
                matches = result.get('matches', [])
                
                key = f"{line}"
                self.grouped_results[key] = {
                    'line': line,
                    'artist': artist,
                    'title': title,
                    'matches': matches,
                    'line_num': result.get('line_num', 0)
                }
            
            self.display_streamlined_results()
            
            # Auto-select best matches if enabled
            settings = QSettings("MusicIndexer", "MusicIndexer")
            if settings.value("auto_select/enabled", True, type=bool):
                # Small delay to ensure UI is ready
                QTimer.singleShot(100, self.auto_select_best_matches)
        else:
            # Regular search results - convert to streamlined format
            self.display_flat_results()
    
    def display_streamlined_results(self):
        """Display streamlined search results in the tree."""
        # Temporarily disable sorting to prevent issues during population
        self.results_tree.setSortingEnabled(False)
        
        # Clear tree
        self.results_tree.clear()
        self.match_dropdowns.clear()
        
        if not self.grouped_results:
            self.status_label.setText("No results to display")
            self.update_button_states()
            return
        
        missing_count = 0
        total_matches = 0
        
        # Sort by line number
        sorted_groups = sorted(
            self.grouped_results.items(), 
            key=lambda x: x[1].get('line_num', 0)
        )
        
        for key, group_data in sorted_groups:
            line = group_data.get('line', '')
            artist = group_data.get('artist', '')
            title = group_data.get('title', '')
            matches = group_data.get('matches', [])
            match_count = len(matches)
            
            # Create tree item
            item = QTreeWidgetItem(self.results_tree)
            
            # Add checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            
            # Set search entry text and track name from original text file
            search_entry = line  # This is the full original line from text file
            original_track_name = line  # Show the exact line from the text file
            if artist and title:
                search_entry = f"{artist} - {title}"
            
            # Set the columns in the new order
            item.setText(1, original_track_name)  # Playlist Entry (2nd column)
            item.setText(2, search_entry)  # Original Search (3rd column)
            
            if match_count == 0:
                # No matches
                item.setText(3, "❌ No matches found")
                item.setForeground(3, QBrush(QColor(200, 0, 0)))
                missing_count += 1
                
                # Store empty data
                item.setData(0, Qt.UserRole + 1, "")  # No file path
                item.setData(0, Qt.UserRole + 2, None)  # No match data
                item.setData(0, Qt.UserRole + 3, [])  # No matches
            else:
                # Has matches - show best match by default
                total_matches += match_count
                best_match = matches[0]
                
                # Update tree item with best match info
                self.update_tree_item_from_match(item, best_match)
                
                # Add search title to match data for display (use original line from text file)
                enhanced_match = best_match.copy()
                enhanced_match['search_title'] = line  # Use the exact original line from text file
                enhanced_match['original_line'] = line  # Store original line as well
                self.update_tree_item_from_match(item, enhanced_match)
                
                # Store match data
                item.setData(0, Qt.UserRole + 1, best_match.get('file_path', ''))
                item.setData(0, Qt.UserRole + 2, best_match)
                item.setData(0, Qt.UserRole + 3, matches)  # Store all matches
                
                # Create dropdown for multiple matches
                if match_count > 1:
                    dropdown = self.create_match_dropdown(matches, item)
                    self.results_tree.setItemWidget(item, 3, dropdown)  # Best Match column (now column 3)
                    
                    # Add indicator for multiple matches
                    score_text = item.text(7)
                    item.setText(7, f"{score_text} ({match_count} matches)")
        
        # Re-enable sorting
        self.results_tree.setSortingEnabled(True)
        
        # Update status
        total_groups = len(self.grouped_results)
        found_groups = total_groups - missing_count
        
        self.status_label.setText(
            f"Displaying {total_groups} search entries: "
            f"{found_groups} found ({total_matches} total matches), "
            f"{missing_count} missing"
        )
        
        self.update_button_states()
    
    def display_flat_results(self):
        """Display regular (non-grouped) search results in the tree."""
        # Temporarily disable sorting
        self.results_tree.setSortingEnabled(False)
        
        # Clear tree
        self.results_tree.clear()
        self.match_dropdowns.clear()
        
        if not self.current_results:
            self.status_label.setText("No results to display")
            self.update_button_states()
            return
        
        # Populate tree with flat results
        for result in self.current_results:
            file_path = result.get('file_path', '')
            filename = os.path.basename(file_path)
            
            item = QTreeWidgetItem(self.results_tree)
            
            # Add checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            
            # Store data
            item.setData(0, Qt.UserRole + 1, file_path)
            item.setData(0, Qt.UserRole + 2, result)
            item.setData(0, Qt.UserRole + 3, [result])  # Single match
            
            # Set display data
            item.setText(1, "Manual Search")  # Playlist Entry (2nd column)
            item.setText(2, "Manual Search")  # Original search (3rd column)
            item.setText(3, filename)  # Best match (4th column)
            item.setText(4, result.get('format', '').upper())
            
            # Duration
            duration = result.get('duration', 0)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_text = f"{minutes}:{seconds:02d}"
            item.setText(5, duration_text)
            
            # Bitrate
            bitrate = result.get('bitrate', 0)
            item.setText(6, f"{bitrate}")
            
            # Match score
            score = result.get('combined_score', 0)
            item.setText(7, f"{score:.1f}%")
            
            # Color code match score
            if score >= 90:
                item.setBackground(7, QColor(200, 255, 200))
            elif score >= 80:
                item.setBackground(7, QColor(220, 255, 220))
            elif score >= 70:
                item.setBackground(7, QColor(255, 255, 200))
            else:
                item.setBackground(7, QColor(255, 220, 220))
        
        # Re-enable sorting
        self.results_tree.setSortingEnabled(True)
        
        # Update status
        self.status_label.setText(f"Displaying {len(self.current_results)} results")
        self.update_button_states()
    
    def update_button_states(self):
        """Update button states based on selection and available results."""
        has_results = self.results_tree.topLevelItemCount() > 0
        has_selections = len(self.auto_selected_files) > 0
        has_grouped_results = bool(self.grouped_results)
        has_auto_search_results = has_grouped_results and getattr(self, 'is_auto_search', False)
        
        # Selection buttons
        self.auto_select_button.setEnabled(has_grouped_results)
        self.select_all_button.setEnabled(has_results)
        self.deselect_all_button.setEnabled(has_results)
        
        # Action buttons
        self.copy_selected_button.setEnabled(has_selections)
        self.show_folder_button.setEnabled(has_selections)
        self.export_button.setEnabled(has_results)
        self.export_missing_button.setEnabled(has_grouped_results and self.has_missing_tracks())
        self.clear_button.setEnabled(has_results)
        
        # Save/Load buttons
        self.save_results_button.setEnabled(has_auto_search_results)
        # Load button is always enabled (no need to set it)
    
    def get_selected_file_paths(self):
        """Get file paths of selected (checked) items."""
        return list(self.auto_selected_files)
    
    def copy_selected_files(self):
        """Copy all selected files to destination folder."""
        if not self.auto_selected_files:
            QMessageBox.warning(self, "No Selection", "No files are selected for copying.")
            return
        
        # Get default export directory from config
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = self.get_app_root_directory()
        
        # Get destination folder
        destination = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder",
            default_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not destination:
            return
        
        # Copy the selected files
        self.copy_files_to_destination(list(self.auto_selected_files), destination)
    
    def copy_files_to_destination(self, file_paths, destination):
        """Copy files to destination with progress dialog."""
        if not os.path.exists(destination):
            try:
                os.makedirs(destination)
                logger.info(f"Created destination directory: {destination}")
            except Exception as e:
                logger.error(f"Failed to create destination directory: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to create destination directory:\n{destination}\n\nError: {str(e)}"
                )
                return
        
        # Create progress dialog
        self.copy_progress = QProgressDialog("Preparing to copy files...", "Cancel", 0, 100, self)
        self.copy_progress.setWindowTitle("Copying Selected Files")
        self.copy_progress.setWindowModality(Qt.NonModal)
        self.copy_progress.setMinimumDuration(0)
        self.copy_progress.setAutoClose(True)
        self.copy_progress.setAutoReset(False)
        
        # Set up copy operation
        total_files = len(file_paths)
        self.copy_progress.setMaximum(total_files)
        self.copy_progress.setValue(0)
        self.copy_progress.show()
        
        # Create timer for non-blocking copy
        self.copy_timer = QTimer()
        self.copy_index = 0
        self.file_paths_to_copy = file_paths
        self.destination_dir = destination
        self.copy_success_count = 0
        self.copy_failed_files = {}
        
        self.copy_timer.timeout.connect(self.copy_next_file)
        self.copy_timer.start(10)
    
    def copy_next_file(self):
        """Copy the next file in the queue."""
        if self.copy_index >= len(self.file_paths_to_copy):
            self.copy_timer.stop()
            self.copy_operation_completed()
            return
        
        src_path = self.file_paths_to_copy[self.copy_index]
        
        try:
            filename = os.path.basename(src_path)
            dest_path = os.path.join(self.destination_dir, filename)
            
            # Update progress
            self.copy_progress.setLabelText(f"Copying {self.copy_index + 1} of {len(self.file_paths_to_copy)}: {filename}")
            
            # Handle duplicate filenames
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(self.destination_dir, f"{base} ({counter}){ext}")
                    counter += 1
            
            # Copy file
            with open(src_path, 'rb') as src_file:
                with open(dest_path, 'wb') as dest_file:
                    dest_file.write(src_file.read())
            
            self.copy_success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to copy file {src_path}: {str(e)}")
            self.copy_failed_files[src_path] = str(e)
        
        # Update progress
        self.copy_index += 1
        self.copy_progress.setValue(self.copy_index)
        
        # Check if canceled
        if self.copy_progress.wasCanceled():
            self.copy_timer.stop()
            self.copy_operation_completed()
    
    def copy_operation_completed(self):
        """Handle copy operation completion."""
        if hasattr(self, 'copy_progress') and self.copy_progress:
            self.copy_progress.close()
        
        total_files = len(self.file_paths_to_copy)
        
        # Show results
        if self.copy_failed_files:
            failed_count = len(self.copy_failed_files)
            error_message = f"Successfully copied {self.copy_success_count} of {total_files} files.\n\n"
            error_message += f"{failed_count} files failed to copy:\n\n"
            
            for path, error in list(self.copy_failed_files.items())[:5]:  # Show first 5 errors
                error_message += f"• {os.path.basename(path)}: {error}\n"
            
            if failed_count > 5:
                error_message += f"... and {failed_count - 5} more files."
            
            QMessageBox.warning(self, "Copy Completed with Errors", error_message)
        else:
            QMessageBox.information(
                self,
                "Copy Complete",
                f"Successfully copied all {self.copy_success_count} selected files to:\n{self.destination_dir}"
            )
    
    def show_context_menu(self, position):
        """Show context menu when right-clicking on a result item."""
        if self.results_tree.topLevelItemCount() == 0:
            return
        
        item = self.results_tree.itemAt(position)
        if not item:
            return
        
        context_menu = QMenu(self)
        
        file_path = item.data(0, Qt.UserRole + 1)
        has_file = bool(file_path)
        
        if has_file:
            # File-specific actions
            show_action = context_menu.addAction("Show in Folder")
            play_action = context_menu.addAction("Play Audio")
            
            # Toggle selection action
            if file_path in self.auto_selected_files:
                select_action = context_menu.addAction("Unselect File")
            else:
                select_action = context_menu.addAction("Select File")
            
            context_menu.addSeparator()
            
            # Connect actions
            show_action.triggered.connect(lambda: self.show_in_folder_single(file_path))
            play_action.triggered.connect(lambda: self.play_audio_file(file_path))
            select_action.triggered.connect(lambda: self.toggle_file_selection(item))
        
        # General actions
        export_action = context_menu.addAction("Export Results")
        export_action.triggered.connect(self.export_results)
        
        # Add missing tracks export for grouped results
        if self.is_auto_search and self.has_missing_tracks():
            export_missing_action = context_menu.addAction("Export Missing Tracks")
            export_missing_action.triggered.connect(self.export_missing_tracks)
        
        # Add save/load options to context menu
        if self.grouped_results and getattr(self, 'is_auto_search', False):
            context_menu.addSeparator()
            
            save_action = context_menu.addAction("Save Auto Search Results")
            save_action.triggered.connect(self.save_auto_search_results)
            
            load_action = context_menu.addAction("Load Auto Search Results")  
            load_action.triggered.connect(self.load_auto_search_results)
        
        clear_action = context_menu.addAction("Clear Results")
        clear_action.triggered.connect(self.clear_results)
        
        context_menu.exec_(QCursor.pos())
    
    def toggle_file_selection(self, item):
        """Toggle selection state of a file item."""
        current_state = item.checkState(0)
        new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
        item.setCheckState(0, new_state)
    
    def show_in_folder(self):
        """Show first selected file in folder."""
        if self.auto_selected_files:
            first_file = next(iter(self.auto_selected_files))
            self.show_in_folder_single(first_file)
    
    def show_in_folder_single(self, file_path):
        """Show specific file in folder."""
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file no longer exists at the specified location:\n{file_path}"
            )
            return
        
        logger.info(f"Showing file in folder: {file_path}")
        
        try:
            if os.name == 'nt':  # Windows
                file_path = os.path.normpath(file_path)
                subprocess.run(['explorer', '/select,', file_path], shell=True)
            elif os.name == 'posix':  # macOS and Linux
                folder_path = os.path.dirname(file_path)
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            logger.error(f"Error showing file in folder: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")
    
    def play_audio_file(self, file_path):
        """Play an audio file using the system's default audio player."""
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file no longer exists at the specified location:\n{file_path}"
            )
            return
        
        logger.info(f"Playing audio file: {file_path}")
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', file_path])
        except Exception as e:
            logger.error(f"Error playing audio file: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not play file: {str(e)}")
    
    def on_item_double_clicked(self, item, column):
        """Handle double-click on an item."""
        file_path = item.data(0, Qt.UserRole + 1)
        if file_path:
            self.play_audio_file(file_path)
    
    def has_missing_tracks(self):
        """Check if there are any missing tracks in the grouped results."""
        if not self.grouped_results:
            return False
        
        for group_data in self.grouped_results.values():
            matches = group_data.get('matches', [])
            if len(matches) == 0:  # No matches = missing track
                return True
        
        return False
    
    def export_missing_tracks(self):
        """Export tracks with no matches to a text file."""
        if not self.grouped_results:
            QMessageBox.information(
                self,
                "No Results",
                "No grouped results available. Please run an automatic search first."
            )
            return
        
        # Collect missing tracks
        missing_tracks = []
        for group_data in self.grouped_results.values():
            matches = group_data.get('matches', [])
            if len(matches) == 0:  # No matches found
                line = group_data.get('line', '')
                artist = group_data.get('artist', '')
                title = group_data.get('title', '')
                
                # Use original line if available, otherwise reconstruct from artist/title
                if line.strip():
                    missing_tracks.append(line.strip())
                elif artist and title:
                    missing_tracks.append(f"{artist} - {title}")
                elif title:  # Only title available
                    missing_tracks.append(title)
        
        if not missing_tracks:
            QMessageBox.information(
                self,
                "No Missing Tracks",
                "Great news! All tracks from your playlist were found in your music collection."
            )
            return
        
        # Get default export directory
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = self.get_app_root_directory()
        
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"missing_tracks_{timestamp}.txt"
        default_path = os.path.join(default_dir, default_filename)
        
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Missing Tracks",
            default_path,
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Determine format based on file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            with open(file_path, 'w', encoding='utf-8') as file:
                if file_ext == '.csv':
                    # CSV format with headers
                    file.write("Original Line,Artist,Title,Status\n")
                    for group_data in self.grouped_results.values():
                        matches = group_data.get('matches', [])
                        if len(matches) == 0:
                            line = group_data.get('line', '')
                            artist = group_data.get('artist', '')
                            title = group_data.get('title', '')
                            
                            # Escape CSV fields
                            line_escaped = f'"{line.replace("\"", "\"\"")}"'
                            artist_escaped = f'"{artist.replace("\"", "\"\"")}"'
                            title_escaped = f'"{title.replace("\"", "\"\"")}"'
                            
                            file.write(f"{line_escaped},{artist_escaped},{title_escaped},Missing\n")
                else:
                    # Simple text format - ready for re-processing
                    file.write("# Missing Tracks - Not found in your music collection\n")
                    file.write("# You can use this file for automatic search after adding more music\n")
                    file.write("# Format: Artist - Title (one per line)\n\n")
                    
                    for track in missing_tracks:
                        file.write(f"{track}\n")
            
            # Show success message with statistics
            total_entries = len(self.grouped_results)
            missing_count = len(missing_tracks)
            found_count = total_entries - missing_count
            
            QMessageBox.information(
                self,
                "Missing Tracks Exported",
                f"✅ Missing tracks exported successfully!\n\n"
                f"📊 Statistics:\n"
                f"• Total playlist entries: {total_entries}\n"
                f"• Found in collection: {found_count}\n"
                f"• Missing tracks: {missing_count}\n"
                f"• Success rate: {(found_count/total_entries*100):.1f}%\n\n"
                f"📁 File saved: {file_path}\n\n"
                f"💡 You can use this file for automatic search after adding more music to your collection!"
            )
            
            logger.info(f"Exported {missing_count} missing tracks to {file_path}")
        
        except Exception as e:
            logger.error(f"Error exporting missing tracks: {str(e)}")
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export missing tracks:\n{str(e)}"
            )
    
    def export_results(self):
        """Export search results to a file."""
        if self.results_tree.topLevelItemCount() == 0:
            return
        
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = self.get_app_root_directory()
        
        default_path = os.path.join(default_dir, "music_search_results.csv")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            default_path,
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                if getattr(self, 'is_auto_search', False):
                    # Export streamlined results with selection status
                    file.write("Selected,Playlist Entry,Original Search,Best Match Filename,Format,Duration,Bitrate,Match Score,Total Matches,File Path\n")
                    
                    for i in range(self.results_tree.topLevelItemCount()):
                        item = self.results_tree.topLevelItem(i)
                        playlist_entry = item.text(1)
                        original_search = item.text(2)
                        best_match_filename = item.text(3)
                        format_type = item.text(4)
                        duration = item.text(5)
                        bitrate = item.text(6)
                        score = item.text(7)
                        file_path_item = item.data(0, Qt.UserRole + 1)
                        matches = item.data(0, Qt.UserRole + 3) or []
                        
                        selected = "Yes" if file_path_item in self.auto_selected_files else "No"
                        
                        file.write(f'"{selected}","{playlist_entry}","{original_search}","{best_match_filename}","{format_type}","{duration}","{bitrate}","{score}",{len(matches)},"{file_path_item}"\n')
                else:
                    # Export flat results
                    file.write("Selected,Playlist Entry,Original Search,Filename,Format,Duration,Bitrate,Match Score,File Path\n")
                    
                    for i in range(self.results_tree.topLevelItemCount()):
                        item = self.results_tree.topLevelItem(i)
                        playlist_entry = item.text(1)
                        original_search = item.text(2)
                        filename = item.text(3)
                        format_type = item.text(4)
                        duration = item.text(5)
                        bitrate = item.text(6)
                        score = item.text(7)
                        file_path_item = item.data(0, Qt.UserRole + 1)
                        
                        selected = "Yes" if file_path_item in self.auto_selected_files else "No"
                        
                        file.write(f'"{selected}","{playlist_entry}","{original_search}","{filename}","{format_type}","{duration}","{bitrate}","{score}","{file_path_item}"\n')
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Results exported to:\n{file_path}"
            )
        
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export results: {str(e)}"
            )
    
    def clear_results(self):
        """Clear search results."""
        self.current_results = []
        self.grouped_results = {}
        self.auto_selected_files.clear()
        self.match_dropdowns.clear()
        self.results_tree.clear()
        self.status_label.setText("No results to display")
        self.update_selection_summary()
        self.update_button_states()
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load column widths
        for i in range(8):  # 8 columns now
            width = settings.value(f"results/column_width_{i}", 0, type=int)
            if width > 0:
                self.results_tree.setColumnWidth(i, width)
        
        # Load sort column and order
        sort_column = settings.value("results/sort_column", 7, type=int)  # Default to score column
        sort_order = settings.value("results/sort_order", Qt.DescendingOrder, type=int)
        self.results_tree.sortByColumn(sort_column, sort_order)
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save column widths
        for i in range(8):  # 8 columns now
            settings.setValue(f"results/column_width_{i}", self.results_tree.columnWidth(i))
        
        # Save sort settings
        header = self.results_tree.header()
        sort_column = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()
        settings.setValue("results/sort_column", sort_column)
        settings.setValue("results/sort_order", sort_order)
    
    def closeEvent(self, event):
        """Handle panel close event."""
        self.save_settings()
        super().closeEvent(event)