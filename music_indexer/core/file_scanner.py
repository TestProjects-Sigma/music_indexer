"""
File scanner module for finding audio files in specified directories.
"""
import os
import time
from tqdm import tqdm

from ..utils.logger import get_logger
logger = get_logger()


class FileScanner:
    """Scans directories for audio files."""
    
    def __init__(self, supported_formats=None):
        """Initialize scanner with supported file formats."""
        self.supported_formats = supported_formats or ["mp3", "flac", "m4a", "aac", "wav"]
        logger.info(f"File scanner initialized with formats: {', '.join(self.supported_formats)}")
    
    def is_supported_format(self, filename):
        """Check if file has a supported audio format."""
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return ext in self.supported_formats
    
    def scan_directory(self, directory_path, recursive=True, show_progress=True):
        """
        Scan a directory for audio files.
        
        Args:
            directory_path (str): Path to directory to scan
            recursive (bool): Whether to scan subdirectories
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of paths to audio files found
        """
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        logger.info(f"Scanning directory: {directory_path}")
        start_time = time.time()
        
        audio_files = []
        
        # First, count files for progress bar
        if show_progress:
            total_files = 0
            for root, _, files in os.walk(directory_path):
                total_files += len(files)
            
            progress_bar = tqdm(total=total_files, desc="Scanning files", unit="file")
        
        # Now scan files
        for root, _, files in os.walk(directory_path):
            for file in files:
                if show_progress:
                    progress_bar.update(1)
                
                if self.is_supported_format(file):
                    file_path = os.path.join(root, file)
                    audio_files.append(file_path)
            
            # If not recursive, break after first iteration
            if not recursive:
                break
        
        if show_progress:
            progress_bar.close()
        
        scan_time = time.time() - start_time
        logger.info(f"Scan completed. Found {len(audio_files)} audio files in {scan_time:.2f} seconds")
        
        return audio_files
    
    def scan_multiple_directories(self, directories, recursive=True, show_progress=True):
        """
        Scan multiple directories for audio files.
        
        Args:
            directories (list): List of directory paths to scan
            recursive (bool): Whether to scan subdirectories
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of paths to audio files found
        """
        all_files = []
        
        for directory in directories:
            files = self.scan_directory(directory, recursive, show_progress)
            all_files.extend(files)
        
        # Remove duplicates while preserving order
        unique_files = []
        for file in all_files:
            if file not in unique_files:
                unique_files.append(file)
        
        return unique_files
