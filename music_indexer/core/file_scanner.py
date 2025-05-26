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

    def scan_directories_parallel(self, directories, callback=None, max_workers=None):
        """
        Scan directories for audio files using parallel processing.
        
        Args:
            directories (list): List of directory paths to scan
            callback (function): Progress callback function
            max_workers (int): Number of parallel workers (None for auto)
        
        Returns:
            list: List of audio file paths found
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import multiprocessing
        import os
        
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), len(directories), 8)
        
        logger.info(f"Starting parallel directory scan with {max_workers} workers")
        
        all_files = []
        total_processed = 0
        
        # If we have fewer directories than workers, scan each directory in parallel
        if len(directories) <= max_workers:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_dir = {executor.submit(self._scan_single_directory, directory): directory 
                               for directory in directories}
                
                for future in as_completed(future_to_dir):
                    directory = future_to_dir[future]
                    try:
                        files = future.result()
                        all_files.extend(files)
                        total_processed += len(files)
                        
                        logger.info(f"Scanned {directory}: found {len(files)} files")
                        
                        if callback:
                            callback(total_processed, f"Scanned {os.path.basename(directory)}")
                            
                    except Exception as e:
                        logger.error(f"Error scanning directory {directory}: {str(e)}")
        else:
            # For many directories, scan them in batches
            for directory in directories:
                files = self._scan_single_directory(directory)
                all_files.extend(files)
                total_processed += len(files)
                
                logger.info(f"Scanned {directory}: found {len(files)} files")
                
                if callback:
                    callback(total_processed, f"Scanned {os.path.basename(directory)}")
        
        logger.info(f"Parallel scan complete: found {len(all_files)} total files")
        return all_files

    def _scan_single_directory(self, directory):
        """
        Scan a single directory for audio files.
        
        Args:
            directory (str): Directory path to scan
        
        Returns:
            list: List of audio file paths in this directory
        """
        files = []
        
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if self._is_audio_file(filename):
                        file_path = os.path.join(root, filename)
                        files.append(file_path)
                        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {str(e)}")
        
        return files