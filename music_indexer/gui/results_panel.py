"""
Results panel GUI with grouped results for the music indexer application.
"""
import os
import sys
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QProgressDialog, QCheckBox,
    QMenu, QStyle
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QColor, QCursor, QIcon, QBrush

from ..utils.logger import get_logger

logger = get_logger()


class ResultsPanel(QWidget):
    """Results panel for the Music Indexer application."""
    
    def __init__(self, music_indexer):
        """Initialize the results panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        self.current_results = []
        self.grouped_results = {}  # Dictionary to store grouped results
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Results panel initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create results tree
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(7)
        self.results_tree.setHeaderLabels([
            "Source/Filename", "Artist", "Title", "Format", "Duration", "Bitrate", "Match Score"
        ])
        
        # Set tree properties
        self.results_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.results_tree.itemExpanded.connect(self.on_item_expanded)
        self.results_tree.itemCollapsed.connect(self.on_item_collapsed)
        
        # Set column widths
        header = self.results_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Source/Filename
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Artist
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Title
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Format
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Bitrate
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Match Score
        
        # Add tree to layout
        main_layout.addWidget(self.results_tree)
        
        # Create status label
        self.status_label = QLabel("No results to display")
        main_layout.addWidget(self.status_label)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Add "Show in Folder" button
        self.show_folder_button = QPushButton("Show in Folder")
        self.show_folder_button.clicked.connect(self.show_in_folder)
        self.show_folder_button.setEnabled(False)
        button_layout.addWidget(self.show_folder_button)
        
        # Add "Copy to Folder" button
        self.copy_button = QPushButton("Copy to Folder")
        self.copy_button.clicked.connect(self.copy_to_folder)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        # Add "Export Results" button
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        # Add "Clear Results" button
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setEnabled(False)
        button_layout.addWidget(self.clear_button)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Connect signals
        self.results_tree.itemSelectionChanged.connect(self.update_button_states)
    
    def on_item_expanded(self, item):
        """Handle item expansion."""
        # Store expanded state
        key = item.data(0, Qt.UserRole)
        if key:
            settings = QSettings("MusicIndexer", "MusicIndexer")
            expanded_items = settings.value("results/expanded_items", [])
            if key not in expanded_items:
                expanded_items.append(key)
            settings.setValue("results/expanded_items", expanded_items)
    
    def on_item_collapsed(self, item):
        """Handle item collapse."""
        # Store collapsed state
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
        
        # Populate tree with grouped results
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
            
            # Store line info in the item's user data
            parent_item.setData(0, Qt.UserRole, key)
            
            # Set item text
            if match_count == 0:
                status_text = "❌ Missing"
                missing_count += 1
                # Red color for missing
                parent_item.setForeground(0, QBrush(QColor(200, 0, 0)))
            else:
                if match_count == 1:
                    status_text = "✓ Found"
                    # Green color for found
                    parent_item.setForeground(0, QBrush(QColor(0, 128, 0)))
                else:
                    status_text = f"⚠ Multiple ({match_count})"
                    # Orange color for multiple
                    parent_item.setForeground(0, QBrush(QColor(255, 140, 0)))
                
                total_matches += match_count
            
            # Set display text for parent item
            parent_item.setText(0, f"{status_text}: {line}")
            parent_item.setText(1, artist)
            parent_item.setText(2, title)
            
            # Add matches as child items
            for match in matches:
                file_path = match.get('file_path', '')
                filename = os.path.basename(file_path)
                
                child_item = QTreeWidgetItem(parent_item)
                child_item.setData(0, Qt.UserRole + 1, file_path)  # Store file path
                
                child_item.setText(0, filename)
                child_item.setText(1, match.get('artist', ''))
                child_item.setText(2, match.get('title', ''))
                child_item.setText(3, match.get('format', ''))
                
                # Duration
                duration = match.get('duration', 0)
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes}:{seconds:02d}"
                child_item.setText(4, duration_text)
                
                # Bitrate
                bitrate = match.get('bitrate', 0)
                child_item.setText(5, f"{bitrate} kbps")
                
                # Match score
                score = match.get('combined_score', 0)
                child_item.setText(6, f"{score:.1f}%")
                
                # Color code match score
                if score >= 90:
                    child_item.setBackground(6, QColor(200, 255, 200))  # Light green
                elif score >= 80:
                    child_item.setBackground(6, QColor(220, 255, 220))  # Lighter green
                elif score >= 70:
                    child_item.setBackground(6, QColor(255, 255, 200))  # Light yellow
                else:
                    child_item.setBackground(6, QColor(255, 220, 220))  # Light red
            
            # Restore expanded state
            if key in expanded_items:
                parent_item.setExpanded(True)
            elif match_count > 0:
                # By default, expand if there are matches
                parent_item.setExpanded(True)
        
        # Update status
        total_groups = len(self.grouped_results)
        found_groups = total_groups - missing_count
        
        self.status_label.setText(
            f"Displaying {total_groups} search entries: "
            f"{found_groups} found ({total_matches} total matches), "
            f"{missing_count} missing"
        )
        
        # Update button states
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
            item.setData(0, Qt.UserRole + 1, file_path)  # Store file path
            
            item.setText(0, filename)
            item.setText(1, result.get('artist', ''))
            item.setText(2, result.get('title', ''))
            item.setText(3, result.get('format', ''))
            
            # Duration
            duration = result.get('duration', 0)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_text = f"{minutes}:{seconds:02d}"
            item.setText(4, duration_text)
            
            # Bitrate
            bitrate = result.get('bitrate', 0)
            item.setText(5, f"{bitrate} kbps")
            
            # Match score
            score = result.get('combined_score', 0)
            item.setText(6, f"{score:.1f}%")
            
            # Color code match score
            if score >= 90:
                item.setBackground(6, QColor(200, 255, 200))  # Light green
            elif score >= 80:
                item.setBackground(6, QColor(220, 255, 220))  # Lighter green
            elif score >= 70:
                item.setBackground(6, QColor(255, 255, 200))  # Light yellow
            else:
                item.setBackground(6, QColor(255, 220, 220))  # Light red
        
        # Update status
        self.status_label.setText(f"Displaying {len(self.current_results)} results")
        
        # Update button states
        self.update_button_states()
    
    def update_button_states(self):
        """Update button states based on selection."""
        selected_items = self.results_tree.selectedItems()
        
        # Check if any file items (not group headers) are selected
        has_file_selection = any(
            item.data(0, Qt.UserRole + 1) is not None 
            for item in selected_items
        )
        
        has_results = self.results_tree.topLevelItemCount() > 0
        
        self.show_folder_button.setEnabled(has_file_selection)
        self.copy_button.setEnabled(has_file_selection)
        self.export_button.setEnabled(has_results)
        self.clear_button.setEnabled(has_results)
    
    def get_selected_file_paths(self):
        """Get file paths of selected items."""
        file_paths = []
        
        # Process all selected items
        for item in self.results_tree.selectedItems():
            # Check if this is a file item (not a group header)
            file_path = item.data(0, Qt.UserRole + 1)
            if file_path:
                file_paths.append(file_path)
            else:
                # It's a group header, add all child file paths
                for i in range(item.childCount()):
                    child = item.child(i)
                    child_path = child.data(0, Qt.UserRole + 1)
                    if child_path:
                        file_paths.append(child_path)
        
        # Remove duplicates while preserving order
        unique_paths = []
        for path in file_paths:
            if path not in unique_paths:
                unique_paths.append(path)
        
        return unique_paths
    
    def show_context_menu(self, position):
        """Show context menu when right-clicking on a result item."""
        # Check if there are any items in the tree
        if self.results_tree.topLevelItemCount() == 0:
            return
        
        # Get the item under cursor
        item = self.results_tree.itemAt(position)
        if not item:
            return
        
        # Check if item is a file or a group header
        is_file_item = item.data(0, Qt.UserRole + 1) is not None
        is_group_item = item.data(0, Qt.UserRole) is not None
        
        # Create context menu
        context_menu = QMenu(self)
        
        if is_file_item:
            # File item menu
            show_action = context_menu.addAction("Show in Folder")
            copy_action = context_menu.addAction("Copy to Export Folder")
            
            # Get default export directory for quick copy
            default_export_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
            
            # Connect actions
            show_action.triggered.connect(self.show_in_folder)
            
            if default_export_dir:
                # If default export directory exists, enable direct copy
                folder_name = os.path.basename(default_export_dir)
                if folder_name:
                    copy_action.setText(f"Copy to Export Folder ({folder_name})")
                copy_action.triggered.connect(lambda: self.copy_to_export_folder(default_export_dir))
            else:
                # Otherwise, use standard copy dialog
                copy_action.triggered.connect(self.copy_to_folder)
        
        if is_group_item:
            # Group item menu
            if item.childCount() > 0:
                if item.isExpanded():
                    expand_action = context_menu.addAction("Collapse")
                    expand_action.triggered.connect(lambda: item.setExpanded(False))
                else:
                    expand_action = context_menu.addAction("Expand")
                    expand_action.triggered.connect(lambda: item.setExpanded(True))
                
                # Add option to expand/collapse all
                context_menu.addSeparator()
                expand_all_action = context_menu.addAction("Expand All")
                expand_all_action.triggered.connect(self.expand_all_groups)
                
                collapse_all_action = context_menu.addAction("Collapse All")
                collapse_all_action.triggered.connect(self.collapse_all_groups)
        
        # Add general actions
        context_menu.addSeparator()
        export_action = context_menu.addAction("Export Results")
        export_action.triggered.connect(self.export_results)
        
        clear_action = context_menu.addAction("Clear Results")
        clear_action.triggered.connect(self.clear_results)
        
        # Show context menu
        context_menu.exec_(QCursor.pos())
    
    def expand_all_groups(self):
        """Expand all group items."""
        root = self.results_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setExpanded(True)
    
    def collapse_all_groups(self):
        """Collapse all group items."""
        root = self.results_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setExpanded(False)
    
    def copy_to_export_folder(self, export_dir):
        """Copy selected files directly to the configured export folder."""
        file_paths = self.get_selected_file_paths()
        
        if not file_paths:
            return
            
        # Check if export directory exists
        if not os.path.exists(export_dir):
            try:
                os.makedirs(export_dir)
                logger.info(f"Created export directory: {export_dir}")
            except Exception as e:
                logger.error(f"Failed to create export directory: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to create export directory:\n{export_dir}\n\nError: {str(e)}"
                )
                return
        
        # Create progress dialog (non-modal)
        from PyQt5.QtCore import QTimer
        
        self.copy_progress = QProgressDialog("Preparing to copy files...", "Cancel", 0, 100, self)
        self.copy_progress.setWindowTitle("Copying")
        self.copy_progress.setWindowModality(Qt.NonModal)  # Make non-modal
        self.copy_progress.setMinimumDuration(0)
        self.copy_progress.setAutoClose(True)
        self.copy_progress.setAutoReset(False)
        
        # Use direct copy operation instead of async method for more reliability
        try:
            # Get total size for progress reporting
            total_files = len(file_paths)
            self.copy_progress.setMaximum(total_files)
            self.copy_progress.setValue(0)
            self.copy_progress.show()
            
            # Create a QTimer to handle copy operations without blocking UI
            self.copy_timer = QTimer()
            self.copy_index = 0
            self.file_paths = file_paths
            self.export_dir = export_dir
            self.copy_success_count = 0
            self.copy_failed_files = {}
            
            # Connect timer to copy next file
            self.copy_timer.timeout.connect(self.copy_next_file)
            self.copy_timer.start(10)  # Start timer
        except Exception as e:
            logger.error(f"Error starting copy operation: {str(e)}")
            QMessageBox.warning(
                self,
                "Copy Failed",
                f"Error starting copy operation: {str(e)}"
            )
    
    def copy_next_file(self):
        """Copy the next file in the queue."""
        # Check if we're done
        if self.copy_index >= len(self.file_paths):
            self.copy_timer.stop()
            self.copy_completed(self.copy_success_count, self.copy_failed_files)
            return
            
        # Get current file path
        src_path = self.file_paths[self.copy_index]
        
        try:
            # Get filename
            filename = os.path.basename(src_path)
            dest_path = os.path.join(self.export_dir, filename)
            
            # Update progress dialog
            self.copy_progress.setLabelText(f"Copying {self.copy_index + 1} of {len(self.file_paths)}: {filename}")
            
            # Check if destination file already exists
            if os.path.exists(dest_path):
                # Append number to filename to make it unique
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(self.export_dir, f"{base} ({counter}){ext}")
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
            self.copy_completed(self.copy_success_count, self.copy_failed_files)
            return
    
    def show_in_folder(self):
        """Show selected file in folder."""
        file_paths = self.get_selected_file_paths()
        
        if not file_paths:
            return
        
        # Get first selected file
        file_path = file_paths[0]
        
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file no longer exists at the specified location:\n{file_path}"
            )
            return
        
        # Log the file path for debugging
        logger.info(f"Showing file in folder: {file_path}")
        
        # Open folder with file selected
        try:
            if os.name == 'nt':  # Windows
                # Ensure the path uses backslashes
                file_path = os.path.normpath(file_path)
                
                # Method 1: Use subprocess with explorer /select
                import subprocess
                subprocess.run(['explorer', '/select,', file_path], shell=True)
                
                # If the above doesn't work, try an alternative approach
                # Method 2: Just open the containing folder
                # folder_path = os.path.dirname(file_path)
                # os.startfile(folder_path)
            
            elif os.name == 'posix':  # macOS and Linux
                folder_path = os.path.dirname(file_path)
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
        
        except Exception as e:
            logger.error(f"Error showing file in folder: {str(e)}")
            
            # Fallback: just open the parent directory
            try:
                folder_path = os.path.dirname(file_path)
                if os.name == 'nt':  # Windows
                    os.startfile(folder_path)
                elif os.name == 'posix':  # macOS and Linux
                    if sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', folder_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', folder_path])
            except Exception as fallback_error:
                logger.error(f"Fallback error: {str(fallback_error)}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not open folder: {str(e)}\nFile path: {file_path}"
                )
    
    def copy_to_folder(self):
        """Copy selected files to a folder."""
        file_paths = self.get_selected_file_paths()
        
        if not file_paths:
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
        
        # Use the copy to export folder method
        self.copy_to_export_folder(destination)

    def copy_completed(self, success_count, failed_files):
        """Handle copy completion."""
        # Close progress dialog
        if hasattr(self, 'copy_progress') and self.copy_progress:
            self.copy_progress.close()
        
        total_files = success_count + len(failed_files)
        
        if failed_files:
            error_message = "The following files could not be copied:\n\n"
            for path, error in failed_files.items():
                error_message += f"{os.path.basename(path)}: {error}\n"
            
            QMessageBox.warning(
                self,
                "Copy Failed",
                error_message
            )
        
        if success_count > 0:
            QMessageBox.information(
                self,
                "Copy Complete",
                f"Successfully copied {success_count} of {total_files} files."
            )
    
    def export_results(self):
        """Export search results to a file."""
        if self.results_tree.topLevelItemCount() == 0:
            return
        
        # Get default export directory from config
        default_dir = self.music_indexer.config_manager.get("paths", "default_export_directory", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
        
        default_path = os.path.join(default_dir, "music_search_results.csv")
        
        # Get file path
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
                    # Export grouped results with status
                    file.write("Status,Source Line,Artist,Title,Match Count,Filename,Format,Duration,Bitrate,Match Score,File Path\n")
                    
                    for i in range(self.results_tree.topLevelItemCount()):
                        parent = self.results_tree.topLevelItem(i)
                        source_line = parent.text(0)
                        artist = parent.text(1)
                        title = parent.text(2)
                        match_count = parent.childCount()
                        
                        if match_count == 0:
                            status = "Missing"
                            # Write header row
                            file.write(f'"{status}","{source_line}","{artist}","{title}",{match_count},"","","","","",""\n')
                        else:
                            if match_count == 1:
                                status = "Found"
                            else:
                                status = "Multiple"
                            
                            # Write header row
                            file.write(f'"{status}","{source_line}","{artist}","{title}",{match_count},"","","","","",""\n')
                            
                            # Write each match
                            for j in range(match_count):
                                child = parent.child(j)
                                filename = child.text(0)
                                child_artist = child.text(1)
                                child_title = child.text(2)
                                format_type = child.text(3)
                                duration = child.text(4)
                                bitrate = child.text(5)
                                score = child.text(6)
                                file_path = child.data(0, Qt.UserRole + 1)
                                
                                # Escape CSV fields
                                filename = f'"{filename.replace("\"", "\"\"")}"'
                                child_artist = f'"{child_artist.replace("\"", "\"\"")}"'
                                child_title = f'"{child_title.replace("\"", "\"\"")}"'
                                file_path = f'"{file_path.replace("\"", "\"\"")}"'
                                
                                # Write match row (with leading commas to align under parent)
                                file.write(f'"","",,,"",{filename},{format_type},{duration},{bitrate},{score},{file_path}\n')
                else:
                    # Export flat results
                    file.write("Filename,Artist,Title,Format,Duration,Bitrate,Match Score,File Path\n")
                    
                    for i in range(self.results_tree.topLevelItemCount()):
                        item = self.results_tree.topLevelItem(i)
                        filename = item.text(0)
                        artist = item.text(1)
                        title = item.text(2)
                        format_type = item.text(3)
                        duration = item.text(4)
                        bitrate = item.text(5)
                        score = item.text(6)
                        file_path = item.data(0, Qt.UserRole + 1)
                        
                        # Escape CSV fields
                        filename = f'"{filename.replace("\"", "\"\"")}"'
                        artist = f'"{artist.replace("\"", "\"\"")}"'
                        title = f'"{title.replace("\"", "\"\"")}"'
                        file_path = f'"{file_path.replace("\"", "\"\"")}"'
                        
                        file.write(f"{filename},{artist},{title},{format_type},{duration},{bitrate},{score},{file_path}\n")
            
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
        self.results_tree.clear()
        self.status_label.setText("No results to display")
        self.update_button_states()
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load column widths
        for i in range(7):  # 7 columns
            width = settings.value(f"results/column_width_{i}", 0, type=int)
            if width > 0:
                self.results_tree.setColumnWidth(i, width)
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save column widths
        for i in range(7):  # 7 columns
            settings.setValue(f"results/column_width_{i}", self.results_tree.columnWidth(i))
        
        # Save expanded state is handled in on_item_expanded/on_item_collapsed
    
    def closeEvent(self, event):
        """Handle panel close event."""
        self.save_settings()
        super().closeEvent(event)