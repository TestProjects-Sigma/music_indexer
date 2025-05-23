"""
Enhanced results panel GUI with auto-selection and bulk operations for the music indexer application.
"""
import os
import sys
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QProgressDialog, QCheckBox,
    QMenu, QStyle, QGroupBox, QButtonGroup
)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QColor, QCursor, QIcon, QBrush

from ..utils.logger import get_logger

logger = get_logger()


class EnhancedResultsPanel(QWidget):
    """Enhanced results panel with auto-selection and bulk operations for the Music Indexer application."""
    
    def __init__(self, music_indexer):
        """Initialize the results panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        self.current_results = []
        self.grouped_results = {}
        self.auto_selected_files = set()  # Track auto-selected files
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Enhanced results panel initialized")
    
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
        
        # Create results tree with checkbox column
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(8)
        self.results_tree.setHeaderLabels([
            "☐", "Source/Filename", "Artist", "Title", "Format", "Duration", "Bitrate", "Match Score"
        ])
        
        # Set tree properties
        self.results_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.results_tree.itemExpanded.connect(self.on_item_expanded)
        self.results_tree.itemCollapsed.connect(self.on_item_collapsed)
        self.results_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.results_tree.itemChanged.connect(self.on_item_changed)
        
        # Set column widths
        header = self.results_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox column
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Source/Filename
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Artist
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Title
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Format
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Bitrate
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Match Score
        
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
        
        min_score = settings.value("auto_select/min_score", 80, type=int)
        format_preferences = settings.value("auto_select/format_preferences", ["flac", "mp3", "m4a", "aac", "wav"])
        prefer_higher_bitrate = settings.value("auto_select/prefer_higher_bitrate", True, type=bool)
        score_tolerance = settings.value("auto_select/score_tolerance", 5, type=int)
        
        # Clear existing selections
        self.deselect_all_matches()
        
        auto_selected_count = 0
        
        # Process each group
        for i in range(self.results_tree.topLevelItemCount()):
            parent_item = self.results_tree.topLevelItem(i)
            
            if parent_item.childCount() == 0:
                continue  # Skip entries with no matches
            
            # Find the best match for this group
            best_match = self.find_best_match(parent_item, min_score, format_preferences, 
                                            prefer_higher_bitrate, score_tolerance)
            
            if best_match:
                # Check the best match
                best_match.setCheckState(0, Qt.Checked)
                file_path = best_match.data(0, Qt.UserRole + 1)
                if file_path:
                    self.auto_selected_files.add(file_path)
                    auto_selected_count += 1
        
        self.update_selection_summary()
        self.update_button_states()
        
        QMessageBox.information(self, "Auto-Selection Complete", 
                              f"Automatically selected {auto_selected_count} best matches based on your preferences.")
    
    def find_best_match(self, parent_item, min_score, format_preferences, prefer_higher_bitrate, score_tolerance):
        """Find the best match for a group based on preferences."""
        candidates = []
        
        # Collect all matches that meet minimum score
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            score_text = child.text(7)  # Match score column
            
            try:
                score = float(score_text.replace('%', ''))
                if score >= min_score:
                    candidates.append({
                        'item': child,
                        'score': score,
                        'format': child.text(4).lower(),  # Format column
                        'bitrate': self.extract_bitrate(child.text(6))  # Bitrate column
                    })
            except (ValueError, AttributeError):
                continue
        
        if not candidates:
            return None
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        best_candidate = candidates[0]
        
        # Check if there are candidates with preferred format within score tolerance
        for candidate in candidates:
            score_diff = best_candidate['score'] - candidate['score']
            
            if score_diff <= score_tolerance:
                # Check format preference
                try:
                    candidate_format_index = format_preferences.index(candidate['format'])
                    best_format_index = format_preferences.index(best_candidate['format']) if best_candidate['format'] in format_preferences else len(format_preferences)
                    
                    # If candidate has better format preference, use it
                    if candidate_format_index < best_format_index:
                        best_candidate = candidate
                        continue
                    
                    # If same format preference and we prefer higher bitrate
                    if (candidate_format_index == best_format_index and 
                        prefer_higher_bitrate and 
                        candidate['bitrate'] > best_candidate['bitrate']):
                        best_candidate = candidate
                        
                except ValueError:
                    # Format not in preferences, skip format comparison
                    if prefer_higher_bitrate and candidate['bitrate'] > best_candidate['bitrate']:
                        best_candidate = candidate
        
        return best_candidate['item']
    
    def extract_bitrate(self, bitrate_text):
        """Extract numeric bitrate from text like '320 kbps'."""
        try:
            return int(bitrate_text.replace(' kbps', '').replace('kbps', ''))
        except (ValueError, AttributeError):
            return 0
    
    def select_all_matches(self):
        """Select all available matches."""
        self.auto_selected_files.clear()
        
        for i in range(self.results_tree.topLevelItemCount()):
            parent_item = self.results_tree.topLevelItem(i)
            
            for j in range(parent_item.childCount()):
                child = parent_item.child(j)
                file_path = child.data(0, Qt.UserRole + 1)
                if file_path:
                    child.setCheckState(0, Qt.Checked)
                    self.auto_selected_files.add(file_path)
        
        self.update_selection_summary()
        self.update_button_states()
    
    def deselect_all_matches(self):
        """Deselect all matches."""
        self.auto_selected_files.clear()
        
        for i in range(self.results_tree.topLevelItemCount()):
            parent_item = self.results_tree.topLevelItem(i)
            
            for j in range(parent_item.childCount()):
                child = parent_item.child(j)
                child.setCheckState(0, Qt.Unchecked)
        
        self.update_selection_summary()
        self.update_button_states()
    
    def copy_selected_files(self):
        """Copy all selected files to destination folder."""
        if not self.auto_selected_files:
            QMessageBox.warning(self, "No Selection", "No files are selected for copying.")
            return
        
        # Get default export directory from config
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
        
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
    
    def on_item_expanded(self, item):
        """Handle item expansion."""
        key = item.data(0, Qt.UserRole)
        if key:
            settings = QSettings("MusicIndexer", "MusicIndexer")
            expanded_items = settings.value("results/expanded_items", [])
            if key not in expanded_items:
                expanded_items.append(key)
            settings.setValue("results/expanded_items", expanded_items)
    
    def on_item_collapsed(self, item):
        """Handle item collapse."""
        key = item.data(0, Qt.UserRole)
        if key:
            settings = QSettings("MusicIndexer", "MusicIndexer")
            expanded_items = settings.value("results/expanded_items", [])
            if key in expanded_items:
                expanded_items.remove(key)
            settings.setValue("results/expanded_items", expanded_items)
    
    def set_results(self, results):
        """Set search results."""
        self.current_results = results
        
        # Clear previous selections
        self.auto_selected_files.clear()
        
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
            
            self.display_grouped_results()
            
            # Auto-select best matches if enabled
            settings = QSettings("MusicIndexer", "MusicIndexer")
            if settings.value("auto_select/enabled", True, type=bool):
                # Small delay to ensure UI is ready
                QTimer.singleShot(100, self.auto_select_best_matches)
        else:
            # Regular search results
            self.display_flat_results()
    
    def display_grouped_results(self):
        """Display grouped search results in the tree."""
        # Clear tree
        self.results_tree.clear()
        
        if not self.grouped_results:
            self.status_label.setText("No results to display")
            self.update_button_states()
            return
        
        # Load expanded state
        settings = QSettings("MusicIndexer", "MusicIndexer")
        expanded_items = settings.value("results/expanded_items", [])
        
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
            
            # Create parent item for the group
            parent_item = QTreeWidgetItem(self.results_tree)
            parent_item.setData(0, Qt.UserRole, key)
            
            # Set item text
            if match_count == 0:
                status_text = "❌ Missing"
                missing_count += 1
                parent_item.setForeground(1, QBrush(QColor(200, 0, 0)))
            else:
                if match_count == 1:
                    status_text = "✓ Found"
                    parent_item.setForeground(1, QBrush(QColor(0, 128, 0)))
                else:
                    status_text = f"⚠ Multiple ({match_count})"
                    parent_item.setForeground(1, QBrush(QColor(255, 140, 0)))
                
                total_matches += match_count
            
            # Set display text for parent item
            parent_item.setText(1, f"{status_text}: {line}")
            parent_item.setText(2, artist)
            parent_item.setText(3, title)
            
            # Add matches as child items
            for match in matches:
                file_path = match.get('file_path', '')
                filename = os.path.basename(file_path)
                
                child_item = QTreeWidgetItem(parent_item)
                child_item.setData(0, Qt.UserRole + 1, file_path)
                
                # Add checkbox
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)
                
                child_item.setText(1, filename)
                child_item.setText(2, match.get('artist', ''))
                child_item.setText(3, match.get('title', ''))
                child_item.setText(4, match.get('format', ''))
                
                # Duration
                duration = match.get('duration', 0)
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes}:{seconds:02d}"
                child_item.setText(5, duration_text)
                
                # Bitrate
                bitrate = match.get('bitrate', 0)
                child_item.setText(6, f"{bitrate} kbps")
                
                # Match score
                score = match.get('combined_score', 0)
                child_item.setText(7, f"{score:.1f}%")
                
                # Color code match score
                if score >= 90:
                    child_item.setBackground(7, QColor(200, 255, 200))
                elif score >= 80:
                    child_item.setBackground(7, QColor(220, 255, 220))
                elif score >= 70:
                    child_item.setBackground(7, QColor(255, 255, 200))
                else:
                    child_item.setBackground(7, QColor(255, 220, 220))
            
            # Restore expanded state
            if key in expanded_items:
                parent_item.setExpanded(True)
            elif match_count > 0:
                parent_item.setExpanded(True)
        
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
        # Clear tree
        self.results_tree.clear()
        
        if not self.current_results:
            self.status_label.setText("No results to display")
            self.update_button_states()
            return
        
        # Populate tree with flat results
        for result in self.current_results:
            file_path = result.get('file_path', '')
            filename = os.path.basename(file_path)
            
            item = QTreeWidgetItem(self.results_tree)
            item.setData(0, Qt.UserRole + 1, file_path)
            
            # Add checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            
            item.setText(1, filename)
            item.setText(2, result.get('artist', ''))
            item.setText(3, result.get('title', ''))
            item.setText(4, result.get('format', ''))
            
            # Duration
            duration = result.get('duration', 0)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_text = f"{minutes}:{seconds:02d}"
            item.setText(5, duration_text)
            
            # Bitrate
            bitrate = result.get('bitrate', 0)
            item.setText(6, f"{bitrate} kbps")
            
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
        
        # Update status
        self.status_label.setText(f"Displaying {len(self.current_results)} results")
        self.update_button_states()
    
    def update_button_states(self):
        """Update button states based on selection and available results."""
        has_results = self.results_tree.topLevelItemCount() > 0
        has_selections = len(self.auto_selected_files) > 0
        has_grouped_results = bool(self.grouped_results)
        
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
    
    def get_selected_file_paths(self):
        """Get file paths of selected (checked) items."""
        return list(self.auto_selected_files)
    
    def show_context_menu(self, position):
        """Show context menu when right-clicking on a result item."""
        if self.results_tree.topLevelItemCount() == 0:
            return
        
        item = self.results_tree.itemAt(position)
        if not item:
            return
        
        is_file_item = item.data(0, Qt.UserRole + 1) is not None
        is_group_item = item.data(0, Qt.UserRole) is not None
        
        context_menu = QMenu(self)
        
        if is_file_item:
            # File item menu
            show_action = context_menu.addAction("Show in Folder")
            play_action = context_menu.addAction("Play Audio")
            
            # Toggle selection action
            file_path = item.data(0, Qt.UserRole + 1)
            if file_path in self.auto_selected_files:
                select_action = context_menu.addAction("Unselect File")
            else:
                select_action = context_menu.addAction("Select File")
            
            # Connect actions
            show_action.triggered.connect(lambda: self.show_in_folder_single(file_path))
            play_action.triggered.connect(lambda: self.play_audio_file(file_path))
            select_action.triggered.connect(lambda: self.toggle_file_selection(item))
        
        if is_group_item:
            # Group item menu
            if item.childCount() > 0:
                if item.isExpanded():
                    expand_action = context_menu.addAction("Collapse")
                    expand_action.triggered.connect(lambda: item.setExpanded(False))
                else:
                    expand_action = context_menu.addAction("Expand")
                    expand_action.triggered.connect(lambda: item.setExpanded(True))
                
                context_menu.addSeparator()
                
                # Group selection actions
                select_best_action = context_menu.addAction("Select Best Match in Group")
                select_all_action = context_menu.addAction("Select All in Group")
                deselect_all_action = context_menu.addAction("Deselect All in Group")
                
                select_best_action.triggered.connect(lambda: self.select_best_in_group(item))
                select_all_action.triggered.connect(lambda: self.select_all_in_group(item))
                deselect_all_action.triggered.connect(lambda: self.deselect_all_in_group(item))
                
                context_menu.addSeparator()
                expand_all_action = context_menu.addAction("Expand All")
                expand_all_action.triggered.connect(self.expand_all_groups)
                
                collapse_all_action = context_menu.addAction("Collapse All")
                collapse_all_action.triggered.connect(self.collapse_all_groups)
        
        # Add general actions
        context_menu.addSeparator()
        export_action = context_menu.addAction("Export Results")
        export_action.triggered.connect(self.export_results)
        
        # Add missing tracks export for grouped results
        if self.is_auto_search and self.has_missing_tracks():
            export_missing_action = context_menu.addAction("Export Missing Tracks")
            export_missing_action.triggered.connect(self.export_missing_tracks)
        
        clear_action = context_menu.addAction("Clear Results")
        clear_action.triggered.connect(self.clear_results)
        
        context_menu.exec_(QCursor.pos())
    
    def toggle_file_selection(self, item):
        """Toggle selection state of a file item."""
        current_state = item.checkState(0)
        new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
        item.setCheckState(0, new_state)
    
    def select_best_in_group(self, group_item):
        """Select the best match in a specific group."""
        if group_item.childCount() == 0:
            return
        
        # Get preferences
        settings = QSettings("MusicIndexer", "MusicIndexer")
        min_score = settings.value("auto_select/min_score", 80, type=int)
        format_preferences = settings.value("auto_select/format_preferences", ["flac", "mp3", "m4a", "aac", "wav"])
        prefer_higher_bitrate = settings.value("auto_select/prefer_higher_bitrate", True, type=bool)
        score_tolerance = settings.value("auto_select/score_tolerance", 5, type=int)
        
        # Deselect all in group first
        self.deselect_all_in_group(group_item)
        
        # Find and select best match
        best_match = self.find_best_match(group_item, min_score, format_preferences, 
                                        prefer_higher_bitrate, score_tolerance)
        if best_match:
            best_match.setCheckState(0, Qt.Checked)
    
    def select_all_in_group(self, group_item):
        """Select all matches in a specific group."""
        for i in range(group_item.childCount()):
            child = group_item.child(i)
            child.setCheckState(0, Qt.Checked)
    
    def deselect_all_in_group(self, group_item):
        """Deselect all matches in a specific group."""
        for i in range(group_item.childCount()):
            child = group_item.child(i)
            child.setCheckState(0, Qt.Unchecked)
    
    def expand_all_groups(self):
        """Expand all group items."""
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            item.setExpanded(True)
    
    def collapse_all_groups(self):
        """Collapse all group items."""
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            item.setExpanded(False)
    
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
            default_dir = os.path.expanduser("~")
        
        # Generate default filename
        from datetime import datetime
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
            default_dir = os.path.expanduser("~")
        
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
                if self.is_auto_search:
                    # Export grouped results with selection status
                    file.write("Status,Selected,Source Line,Artist,Title,Match Count,Filename,Format,Duration,Bitrate,Match Score,File Path\n")
                    
                    for i in range(self.results_tree.topLevelItemCount()):
                        parent = self.results_tree.topLevelItem(i)
                        source_line = parent.text(1)
                        artist = parent.text(2)
                        title = parent.text(3)
                        match_count = parent.childCount()
                        
                        if match_count == 0:
                            status = "Missing"
                            file.write(f'"{status}","No","Line {source_line}","{artist}","{title}",{match_count},"","","","","",""\n')
                        else:
                            if match_count == 1:
                                status = "Found"
                            else:
                                status = "Multiple"
                            
                            file.write(f'"{status}","Header","Line {source_line}","{artist}","{title}",{match_count},"","","","","",""\n')
                            
                            for j in range(match_count):
                                child = parent.child(j)
                                filename = child.text(1)
                                child_artist = child.text(2)
                                child_title = child.text(3)
                                format_type = child.text(4)
                                duration = child.text(5)
                                bitrate = child.text(6)
                                score = child.text(7)
                                file_path_item = child.data(0, Qt.UserRole + 1)
                                
                                selected = "Yes" if file_path_item in self.auto_selected_files else "No"
                                
                                file.write(f'"","Selected: {selected}","","{child_artist}","{child_title}","","{filename}","{format_type}","{duration}","{bitrate}","{score}","{file_path_item}"\n')
                else:
                    # Export flat results
                    file.write("Selected,Filename,Artist,Title,Format,Duration,Bitrate,Match Score,File Path\n")
                    
                    for i in range(self.results_tree.topLevelItemCount()):
                        item = self.results_tree.topLevelItem(i)
                        filename = item.text(1)
                        artist = item.text(2)
                        title = item.text(3)
                        format_type = item.text(4)
                        duration = item.text(5)
                        bitrate = item.text(6)
                        score = item.text(7)
                        file_path_item = item.data(0, Qt.UserRole + 1)
                        
                        selected = "Yes" if file_path_item in self.auto_selected_files else "No"
                        
                        file.write(f'"{selected}","{filename}","{artist}","{title}","{format_type}","{duration}","{bitrate}","{score}","{file_path_item}"\n')
            
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
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save column widths
        for i in range(8):  # 8 columns now
            settings.setValue(f"results/column_width_{i}", self.results_tree.columnWidth(i))
    
    def closeEvent(self, event):
        """Handle panel close event."""
        self.save_settings()
        super().closeEvent(event)