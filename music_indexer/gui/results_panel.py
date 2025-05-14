"""
Results panel GUI for the music indexer application.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QProgressDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QColor

from ..utils.logger import get_logger

logger = get_logger()


class ResultsPanel(QWidget):
    """Results panel for the Music Indexer application."""
    
    def __init__(self, music_indexer):
        """Initialize the results panel."""
        super().__init__()
        
        self.music_indexer = music_indexer
        self.current_results = []
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Results panel initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create results table
        self.results_table = QTableWidget(0, 7)
        self.results_table.setHorizontalHeaderLabels([
            "Filename", "Artist", "Title", "Format", "Duration", "Bitrate", "Match Score"
        ])
        
        # Set table properties
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_table.setAlternatingRowColors(True)
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Filename
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Artist
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Title
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Format
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Bitrate
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Match Score
        
        # Enable sorting
        self.results_table.setSortingEnabled(True)
        
        # Add table to layout
        main_layout.addWidget(self.results_table)
        
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
        self.results_table.itemSelectionChanged.connect(self.update_button_states)
    
    def set_results(self, results):
        """Set search results."""
        self.current_results = results
        self.display_results()
    
    def display_results(self):
        """Display search results in the table."""
        # Clear table
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        
        if not self.current_results:
            self.status_label.setText("No results to display")
            self.update_button_states()
            return
        
        # Populate table
        for row, result in enumerate(self.current_results):
            self.results_table.insertRow(row)
            
            file_path = result.get('file_path', '')
            
            # Filename
            filename = os.path.basename(file_path)
            filename_item = QTableWidgetItem(filename)
            filename_item.setData(Qt.UserRole, file_path)
            # Add tooltip to show full path
            filename_item.setToolTip(file_path)
            self.results_table.setItem(row, 0, filename_item)
            
            # Artist
            artist = result.get('artist', '')
            artist_item = QTableWidgetItem(artist)
            self.results_table.setItem(row, 1, artist_item)
            
            # Title
            title = result.get('title', '')
            title_item = QTableWidgetItem(title)
            self.results_table.setItem(row, 2, title_item)
            
            # Format
            format_type = result.get('format', '')
            format_item = QTableWidgetItem(format_type)
            self.results_table.setItem(row, 3, format_item)
            
            # Duration
            duration = result.get('duration', 0)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_text = f"{minutes}:{seconds:02d}"
            duration_item = QTableWidgetItem(duration_text)
            duration_item.setData(Qt.UserRole, duration)  # Store raw duration for sorting
            self.results_table.setItem(row, 4, duration_item)
            
            # Bitrate
            bitrate = result.get('bitrate', 0)
            bitrate_text = f"{bitrate} kbps"
            bitrate_item = QTableWidgetItem(bitrate_text)
            bitrate_item.setData(Qt.UserRole, bitrate)  # Store raw bitrate for sorting
            self.results_table.setItem(row, 5, bitrate_item)
            
            # Match Score
            score = result.get('combined_score', 0)
            score_text = f"{score:.1f}%"
            score_item = QTableWidgetItem(score_text)
            score_item.setData(Qt.UserRole, score)  # Store raw score for sorting
            
            # Color code match score
            if score >= 90:
                score_item.setBackground(QColor(200, 255, 200))  # Light green
            elif score >= 80:
                score_item.setBackground(QColor(220, 255, 220))  # Lighter green
            elif score >= 70:
                score_item.setBackground(QColor(255, 255, 200))  # Light yellow
            else:
                score_item.setBackground(QColor(255, 220, 220))  # Light red
            
            self.results_table.setItem(row, 6, score_item)
        
        # Update status
        self.status_label.setText(f"Displaying {len(self.current_results)} results")
        
        # Re-enable sorting
        self.results_table.setSortingEnabled(True)
        
        # Update button states
        self.update_button_states()
    
    def update_button_states(self):
        """Update button states based on selection."""
        has_results = len(self.current_results) > 0
        has_selection = len(self.results_table.selectedItems()) > 0
        
        self.show_folder_button.setEnabled(has_selection)
        self.copy_button.setEnabled(has_selection)
        self.export_button.setEnabled(has_results)
        self.clear_button.setEnabled(has_results)
    
    def get_selected_file_paths(self):
        """Get file paths of selected rows."""
        file_paths = []
        
        # Get selected rows
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        # Get file paths
        for row in selected_rows:
            file_path = self.results_table.item(row, 0).data(Qt.UserRole)
            file_paths.append(file_path)
        
        return file_paths
    
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
     
        # Create progress dialog (non-modal)
        self.copy_progress = QProgressDialog("Copying files...", "Cancel", 0, 100, self)
        self.copy_progress.setWindowTitle("Copying")
        self.copy_progress.setWindowModality(Qt.NonModal)  # Make non-modal
        self.copy_progress.setMinimumDuration(0)
        self.copy_progress.setAutoClose(False)
        self.copy_progress.setAutoReset(False)
        
        # Create a copy worker using Qt's thread pool
        from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
        
        class CopyWorker(QRunnable):
            """Worker for copying files in a separate thread."""
            
            class Signals(QObject):
                """Worker signals."""
                progress = pyqtSignal(float, str)
                finished = pyqtSignal(int, dict)
                
            def __init__(self, file_paths, destination):
                """Initialize the worker."""
                super().__init__()
                self.file_paths = file_paths
                self.destination = destination
                self.signals = self.Signals()
                self.cancelled = False
            
            @pyqtSlot()
            def run(self):
                """Run the worker."""
                success_count = 0
                failed_files = {}
                total_files = len(self.file_paths)
                
                for i, src_path in enumerate(self.file_paths):
                    if self.cancelled:
                        break
                    
                    try:
                        # Get filename
                        filename = os.path.basename(src_path)
                        dest_path = os.path.join(self.destination, filename)
                        
                        # Check if destination file already exists
                        if os.path.exists(dest_path):
                            # Append number to filename to make it unique
                            base, ext = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(dest_path):
                                dest_path = os.path.join(self.destination, f"{base} ({counter}){ext}")
                                counter += 1
                        
                        # Copy file
                        with open(src_path, 'rb') as src_file:
                            with open(dest_path, 'wb') as dest_file:
                                dest_file.write(src_file.read())
                        
                        success_count += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to copy file {src_path}: {str(e)}")
                        failed_files[src_path] = str(e)
                    
                    # Report progress
                    progress = (i + 1) / total_files * 100
                    self.signals.progress.emit(progress, f"Copied {i + 1} of {total_files} files")
                
                self.signals.finished.emit(success_count, failed_files)
        
        # Create worker
        worker = CopyWorker(file_paths, destination)
        
        # Connect signals
        worker.signals.progress.connect(self.update_copy_progress)
        worker.signals.finished.connect(self.copy_completed)
        
        # Handle cancel button
        self.copy_progress.canceled.connect(lambda: setattr(worker, 'cancelled', True))
        
        # Start worker
        QThreadPool.globalInstance().start(worker)
        
        # Show the dialog after starting the thread
        self.copy_progress.show()

    def update_copy_progress(self, value, message):
        """Update copy progress dialog."""
        if hasattr(self, 'copy_progress') and self.copy_progress:
            self.copy_progress.setValue(int(value))
            self.copy_progress.setLabelText(message)

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
        if not self.current_results:
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
                # Write header
                file.write("Filename,Artist,Title,Format,Duration,Bitrate,Match Score,File Path\n")
                
                # Write data
                for result in self.current_results:
                    filename = os.path.basename(result.get('file_path', ''))
                    artist = result.get('artist', '')
                    title = result.get('title', '')
                    format_type = result.get('format', '')
                    duration = result.get('duration', 0)
                    bitrate = result.get('bitrate', 0)
                    score = result.get('combined_score', 0)
                    file_path = result.get('file_path', '')
                    
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
        self.results_table.setRowCount(0)
        self.status_label.setText("No results to display")
        self.update_button_states()
    
    def load_settings(self):
        """Load panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Load column widths
        for i in range(self.results_table.columnCount()):
            width = settings.value(f"results/column_width_{i}", 0, type=int)
            if width > 0:
                self.results_table.setColumnWidth(i, width)
    
    def save_settings(self):
        """Save panel settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        # Save column widths
        for i in range(self.results_table.columnCount()):
            settings.setValue(f"results/column_width_{i}", self.results_table.columnWidth(i))
    
    def closeEvent(self, event):
        """Handle panel close event."""
        self.save_settings()
        super().closeEvent(event)
