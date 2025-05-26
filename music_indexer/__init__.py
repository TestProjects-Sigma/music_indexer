"""
Main application module for the music indexer.
"""
import os
import threading

from .core.file_scanner import FileScanner
from .core.metadata_extractor import MetadataExtractor
from .core.cache_manager import CacheManager
from .search.manual_search import ManualSearch
from .search.auto_search import AutoSearch
from .search.string_matcher import StringMatcher
from .utils.config_manager import ConfigManager
from .utils.logger import get_logger
from .utils.smart_auto_selector import SmartAutoSelector

logger = get_logger()


class MusicIndexer:
    """
    Main application class for the music indexer.
    """
    
    def __init__(self):
        """Initialize the music indexer application."""
        # Initialize components
        self.config_manager = ConfigManager()
        self.file_scanner = FileScanner(self.config_manager.get_supported_formats())
        self.metadata_extractor = MetadataExtractor()
        self.cache_manager = CacheManager(self.config_manager.get("indexing", "cache_file"))
        self.string_matcher = StringMatcher(self.config_manager.get_similarity_threshold())
        self.manual_search = ManualSearch(self.cache_manager, self.string_matcher)
        self.auto_search = AutoSearch(self.cache_manager, self.string_matcher)
        self.smart_auto_selector = SmartAutoSelector()
        
        # Initialize state
        self.indexing_in_progress = False
        self.search_in_progress = False
        self.current_search_results = []
        
        logger.info("Music Indexer application initialized")
    
    def get_music_directories(self):
        """
        Get configured music directories.
        
        Returns:
            list: List of configured music directories
        """
        return self.config_manager.get("paths", "music_directories", [])
    
    def add_music_directory(self, directory):
        """
        Add a music directory to configuration.
        
        Args:
            directory (str): Directory to add
        
        Returns:
            bool: True if directory was added successfully, False otherwise
        """
        return self.config_manager.add_music_directory(directory)
    
    def remove_music_directory(self, directory):
        """
        Remove a music directory from configuration.
        
        Args:
            directory (str): Directory to remove
        
        Returns:
            bool: True if directory was removed successfully, False otherwise
        """
        return self.config_manager.remove_music_directory(directory)
  
    def index_files(self, directories=None, extract_audio_metadata=True, progress_callback=None):
        """
        Index audio files from specified directories using parallel processing.
        
        Args:
            directories (list): List of directories to scan
            extract_audio_metadata (bool): Whether to extract audio metadata
            progress_callback (function): Progress update callback
        
        Returns:
            dict: Results summary
        """
        import time
        
        if directories is None:
            directories = self.config_manager.get_music_directories()
        
        if not directories:
            logger.warning("No directories specified for indexing")
            return {'success': False, 'message': 'No directories specified'}
        
        start_time = time.time()
        mode = "full metadata" if extract_audio_metadata else "fast mode"
        logger.info(f"Starting parallel indexing in {mode}")
        
        # Phase 1: Scan directories for files (parallel)
        if progress_callback:
            progress_callback(0, "Scanning directories for audio files...")
        
        audio_files = self.file_scanner.scan_directories_parallel(
            directories, 
            callback=lambda count, msg: progress_callback(count, f"Scanning: {msg}") if progress_callback else None
        )
        
        if not audio_files:
            logger.warning("No audio files found in specified directories")
            return {'success': False, 'message': 'No audio files found'}
        
        logger.info(f"Found {len(audio_files)} audio files to process")
        
        # Phase 2: Filter out already indexed files
        if progress_callback:
            progress_callback(len(audio_files), "Checking for existing files...")
        
        # Get existing files from cache
        existing_files = set()
        try:
            cached_files = self.cache_manager.get_all_files()
            existing_files = {f.get('file_path', '') for f in cached_files}
            logger.info(f"Found {len(existing_files)} already indexed files")
        except Exception as e:
            logger.warning(f"Could not load existing files: {str(e)}")
        
        # Filter to only new files
        new_files = [f for f in audio_files if f not in existing_files]
        
        if not new_files:
            logger.info("All files are already indexed")
            return {
                'success': True, 
                'message': f'All {len(audio_files)} files already indexed',
                'total_files': len(audio_files),
                'new_files': 0,
                'processing_time': time.time() - start_time
            }
        
        logger.info(f"Processing {len(new_files)} new files ({len(audio_files) - len(new_files)} already indexed)")
        
        # Phase 3: Extract metadata in parallel
        if progress_callback:
            progress_callback(0, f"Extracting metadata from {len(new_files)} new files...")
        
        metadata_list = self.metadata_extractor.extract_metadata_parallel(
            new_files,
            extract_audio_metadata=extract_audio_metadata,
            callback=lambda count, msg: progress_callback(count, msg) if progress_callback else None
        )
        
        # Phase 4: Store in cache
        if progress_callback:
            progress_callback(len(metadata_list), "Storing metadata in database...")
        
        stored_count = 0
        for metadata in metadata_list:
            if metadata and self.cache_manager.store_file_metadata(metadata):
                stored_count += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        result = {
            'success': True,
            'message': f'Successfully indexed {stored_count} new files',
            'total_files': len(audio_files),
            'new_files': stored_count,
            'already_indexed': len(existing_files),
            'processing_time': processing_time
        }
        
        logger.info(f"Parallel indexing complete: {stored_count} files processed in {processing_time:.2f} seconds")
        return result  
     
    def index_files_async(self, recursive=True, extract_metadata=True, callback=None, complete_callback=None):
        """
        Index music files asynchronously using Qt's thread pool.
        
        Args:
            recursive (bool): Whether to scan subdirectories
            extract_metadata (bool): Whether to extract full audio metadata (slower) or just basic file info
            callback (function): Optional callback function to report progress
            complete_callback (function): Optional callback function called when indexing completes
        """
        # Create worker
        worker = IndexingWorker(self, recursive, extract_metadata)
        
        # Connect signals
        if callback:
            worker.signals.progress.connect(callback)
        if complete_callback:
            worker.signals.finished.connect(complete_callback)
        
        # Start worker
        QThreadPool.globalInstance().start(worker)
        logger.info(f"Started indexing worker with extract_metadata={extract_metadata}")
        
        # Store worker reference to prevent garbage collection
        self._current_worker = worker
    
    def search_files(self, query=None, artist=None, title=None, album=None, format_type=None, exact_match=False):
        """
        Search for music files based on specified criteria.
        
        Args:
            query (str): General search query (searches across artist, title, album)
            artist (str): Artist name to match
            title (str): Title to match
            album (str): Album to match
            format_type (str): File format to match
            exact_match (bool): Whether to use exact matching (SQL LIKE) or fuzzy matching
        
        Returns:
            list: List of matching file metadata
        """
        self.search_in_progress = True
        
        try:
            results = self.manual_search.search(
                query=query,
                artist=artist,
                title=title,
                album=album,
                format_type=format_type,
                exact_match=exact_match
            )
            
            self.current_search_results = results
            self.search_in_progress = False
            return results
        
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            self.search_in_progress = False
            return []
    
    def process_match_file(self, file_path, show_progress=True):
        """
        Process a match file and find matches for each entry.
        
        Args:
            file_path (str): Path to match file
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of results for each line
        """
        self.search_in_progress = True
        
        try:
            results = self.auto_search.process_match_file(file_path, show_progress)
            self.search_in_progress = False
            return results
        
        except Exception as e:
            logger.error(f"Error processing match file: {str(e)}")
            self.search_in_progress = False
            return []
    
    def process_match_file_async(self, file_path, callback=None, show_progress=True):
        """
        Process a match file asynchronously in a separate thread.
        
        Args:
            file_path (str): Path to match file
            callback (function): Callback function called with results when processing completes
            show_progress (bool): Whether to show progress bar
        """
        def run_processing():
            results = self.process_match_file(file_path, show_progress)
            if callback:
                callback(results)
        
        thread = threading.Thread(target=run_processing)
        thread.daemon = True
        thread.start()
    
    def save_match_results(self, results, output_file):
        """
        Save match results to a file.
        
        Args:
            results (list): List of match results
            output_file (str): Path to output file
        
        Returns:
            bool: True if results were saved successfully, False otherwise
        """
        return self.auto_search.save_results(results, output_file)

    def update_auto_selection_preferences(self, **kwargs):
        """Update auto-selection preferences."""
        self.smart_auto_selector.update_preferences(**kwargs)
    
    def copy_files_to_directory(self, file_paths, target_directory, callback=None):
        """
        Copy selected files to a target directory.
        
        Args:
            file_paths (list): List of file paths to copy
            target_directory (str): Target directory
            callback (function): Optional callback function to report progress
        
        Returns:
            tuple: (success_count, failed_files) where failed_files is a dict of path:error
        """
        if not os.path.exists(target_directory):
            try:
                os.makedirs(target_directory)
            except Exception as e:
                logger.error(f"Failed to create target directory {target_directory}: {str(e)}")
                return 0, {target_directory: str(e)}
        
        success_count = 0
        failed_files = {}
        total_files = len(file_paths)
        
        for i, src_path in enumerate(file_paths):
            try:
                # Get filename
                filename = os.path.basename(src_path)
                dest_path = os.path.join(target_directory, filename)
                
                # Check if destination file already exists
                if os.path.exists(dest_path):
                    # Append number to filename to make it unique
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(target_directory, f"{base} ({counter}){ext}")
                        counter += 1
                
                # Copy file
                with open(src_path, 'rb') as src_file:
                    with open(dest_path, 'wb') as dest_file:
                        dest_file.write(src_file.read())
                
                success_count += 1
                
                # Report progress if callback provided
                if callback:
                    progress = (i + 1) / total_files * 100
                    callback(progress, f"Copied {i + 1} of {total_files} files")
            
            except Exception as e:
                logger.error(f"Failed to copy file {src_path}: {str(e)}")
                failed_files[src_path] = str(e)
        
        logger.info(f"Copied {success_count} of {total_files} files to {target_directory}")
        return success_count, failed_files
    
    def copy_files_async(self, file_paths, target_directory, callback=None, complete_callback=None):
        """
        Copy files asynchronously in a separate thread.
        
        Args:
            file_paths (list): List of file paths to copy
            target_directory (str): Target directory
            callback (function): Optional callback function to report progress
            complete_callback (function): Optional callback function called when copying completes
        """
        def run_copying():
            result = self.copy_files_to_directory(file_paths, target_directory, callback)
            if complete_callback:
                complete_callback(*result)
        
        thread = threading.Thread(target=run_copying)
        thread.daemon = True
        thread.start()
    
    def get_cache_stats(self):
        """
        Get statistics about the cache.
        
        Returns:
            dict: Cache statistics
        """
        return self.cache_manager.get_cache_stats()
    
    def clear_cache(self):
        """
        Clear all cached file metadata.
        
        Returns:
            bool: True if cache was cleared successfully, False otherwise
        """
        return self.cache_manager.clear_cache()
    
    def set_similarity_threshold(self, threshold):
        """
        Set the similarity threshold for fuzzy matching.
        
        Args:
            threshold (int): New similarity threshold (0-100)
        """
        threshold = max(0, min(100, int(threshold)))
        self.string_matcher.set_threshold(threshold)
        self.config_manager.set_similarity_threshold(threshold)

    def index_files(self, recursive=True, extract_metadata=True, callback=None):
        """
        Index music files in configured directories.
        
        Args:
            recursive (bool): Whether to scan subdirectories
            extract_metadata (bool): Whether to extract full audio metadata (slower) or just basic file info
            callback (function): Optional callback function to report progress
        
        Returns:
            bool: True if indexing completed successfully, False otherwise
        """
        if self.indexing_in_progress:
            logger.warning("Indexing already in progress")
            return False
        
        self.indexing_in_progress = True
        
        try:
            # Get music directories
            directories = self.get_music_directories()
            
            if not directories:
                logger.warning("No music directories configured")
                self.indexing_in_progress = False
                return False
            
            # Scan directories for audio files
            logger.info(f"Starting file scan in {len(directories)} directories")
            audio_files = self.file_scanner.scan_multiple_directories(directories, recursive)
            
            if not audio_files:
                logger.warning("No audio files found in configured directories")
                self.indexing_in_progress = False
                return False
            
            logger.info(f"Found {len(audio_files)} audio files")
            
            # Clean missing files from cache
            self.cache_manager.clean_missing_files()
            
            # Extract metadata and cache
            logger.info(f"Extracting {'full' if extract_metadata else 'basic'} metadata and updating cache")
            
            total_files = len(audio_files)
            
            # Process files one by one
            for i, file_path in enumerate(audio_files):
                # Extract metadata based on the extract_metadata flag
                if extract_metadata:
                    metadata = self.metadata_extractor.extract_metadata(file_path)
                else:
                    metadata = self.metadata_extractor.extract_basic_metadata(file_path)
                
                if metadata:
                    # Cache metadata directly
                    self.cache_manager.cache_file_metadata(metadata)
                
                # Report progress
                if callback:
                    progress = (i + 1) / total_files * 100
                    callback(progress, f"Processed {i + 1} of {total_files} files")
            
            # Get cache stats
            stats = self.cache_manager.get_cache_stats()
            logger.info(f"Indexing completed. Cache contains {stats['total_files']} files")
            
            self.indexing_in_progress = False
            return True
        
        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.indexing_in_progress = False
            return False

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

class IndexingWorker(QRunnable):
    """Worker for indexing files in a separate thread using Qt's thread pool."""
    
    class Signals(QObject):
        """Worker signals."""
        progress = pyqtSignal(float, str)
        finished = pyqtSignal(bool)
        
    def __init__(self, music_indexer, recursive=True, extract_metadata=True):
        """Initialize the worker."""
        super().__init__()
        self.music_indexer = music_indexer
        self.recursive = recursive
        self.extract_metadata = extract_metadata
        self.signals = self.Signals()
        self.cancelled = False
    
    @pyqtSlot()
    def run(self):
        """Run the worker."""
        try:
            # Get music directories
            directories = self.music_indexer.get_music_directories()
            
            if not directories:
                logger.warning("No music directories configured")
                self.signals.finished.emit(False)
                return
            
            # Scan directories for audio files
            logger.info(f"Starting file scan in {len(directories)} directories")
            audio_files = self.music_indexer.file_scanner.scan_multiple_directories(
                directories, self.recursive)
            
            if not audio_files:
                logger.warning("No audio files found in configured directories")
                self.signals.finished.emit(False)
                return
            
            logger.info(f"Found {len(audio_files)} audio files")
            
            # Clean missing files from cache
            self.music_indexer.cache_manager.clean_missing_files()
            
            # Extract metadata and cache
            logger.info(f"Extracting {'full' if self.extract_metadata else 'basic'} metadata and updating cache")
            
            total_files = len(audio_files)
            
            # Process files one by one
            for i, file_path in enumerate(audio_files):
                if self.cancelled:
                    logger.info("Indexing cancelled")
                    self.signals.finished.emit(False)
                    return
                
                # Extract metadata based on the extract_metadata flag
                if self.extract_metadata:
                    metadata = self.music_indexer.metadata_extractor.extract_metadata(file_path)
                else:
                    metadata = self.music_indexer.metadata_extractor.extract_basic_metadata(file_path)
                
                if metadata:
                    # Cache metadata directly
                    self.music_indexer.cache_manager.cache_file_metadata(metadata)
                
                # Report progress
                progress = (i + 1) / total_files * 100
                self.signals.progress.emit(progress, f"Processed {i + 1} of {total_files} files")
            
            # Get cache stats
            stats = self.music_indexer.cache_manager.get_cache_stats()
            logger.info(f"Indexing completed. Cache contains {stats['total_files']} files")
            
            self.signals.finished.emit(True)
        
        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.signals.finished.emit(False)