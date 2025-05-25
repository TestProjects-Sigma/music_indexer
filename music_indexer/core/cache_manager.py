"""
Cache manager for storing and retrieving audio file metadata using SQLite.
"""
import os
import sqlite3
import json
import time
from tqdm import tqdm

from ..utils.logger import get_logger

logger = get_logger()


class CacheManager:
    """Manages caching of audio file metadata using SQLite."""
    
    def __init__(self, cache_file="cache/music_cache.db"):
        """Initialize the cache manager with specified cache file."""
        self.cache_file = cache_file
        self._ensure_cache_dir()
        self._init_database()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _init_database(self):
        """Initialize the database schema."""
        try:
            logger.info(f"Initializing database: {self.cache_file}")
            
            conn = sqlite3.connect(self.cache_file, timeout=30.0)  # 30 second timeout
            conn.execute("PRAGMA journal_mode=WAL")  # Use WAL mode for better concurrency
            conn.execute("PRAGMA synchronous=NORMAL")  # Compromise between safety and speed
            
            cursor = conn.cursor()
            
            # Create files table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                filename TEXT,
                format TEXT,
                duration REAL,
                bitrate INTEGER,
                sample_rate INTEGER,
                channels INTEGER,
                artist TEXT,
                title TEXT,
                album TEXT,
                year TEXT,
                genre TEXT,
                artist_from_filename BOOLEAN,
                title_from_filename BOOLEAN,
                bits_per_sample INTEGER,
                last_modified REAL,
                last_scanned REAL,
                extra_data TEXT
            )
            ''')
            
            # Create index on file_path for faster lookups
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file_path ON files(file_path)
            ''')
            
            # Create indexes on commonly searched fields for exact matching
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_artist ON files(artist)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON files(title)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_album ON files(album)')

            # Create indexes for case-insensitive LIKE queries (used in pre-filtering)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_artist_lower ON files(LOWER(artist))')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_title_lower ON files(LOWER(title))')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_filename_lower ON files(LOWER(filename))')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {str(e)}")

    
    def cache_file_metadata(self, metadata):
        """
        Cache metadata for a single audio file.
        
        Args:
            metadata (dict): Metadata dictionary for the file
        
        Returns:
            bool: True if metadata was cached successfully, False otherwise
        """
        if not metadata or 'file_path' not in metadata:
            logger.error("Invalid metadata: missing file_path")
            return False
        
        try:
            logger.debug(f"Attempting to cache metadata for: {metadata.get('file_path', 'unknown')}")
            
            conn = sqlite3.connect(self.cache_file, timeout=20.0)  # Increase timeout
            cursor = conn.cursor()
            
            # Extract fields from metadata
            file_path = metadata['file_path']
            filename = metadata.get('filename', os.path.basename(file_path))
            format_type = metadata.get('format', '')
            duration = metadata.get('duration', 0)
            bitrate = metadata.get('bitrate', 0)
            sample_rate = metadata.get('sample_rate', 0)
            channels = metadata.get('channels', 0)
            artist = metadata.get('artist', '')
            title = metadata.get('title', '')
            album = metadata.get('album', '')
            year = metadata.get('year', '')
            genre = metadata.get('genre', '')
            artist_from_filename = metadata.get('artist_from_filename', False)
            title_from_filename = metadata.get('title_from_filename', False)
            bits_per_sample = metadata.get('bits_per_sample', 0)
            basic_metadata_only = metadata.get('basic_metadata_only', False)
            
            # Get file modification time
            last_modified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
            last_scanned = time.time()
            
            # Store additional metadata as JSON
            extra_data = {}
            for key, value in metadata.items():
                if key not in [
                    'file_path', 'filename', 'format', 'duration', 'bitrate', 
                    'sample_rate', 'channels', 'artist', 'title', 'album', 
                    'year', 'genre', 'artist_from_filename', 'title_from_filename',
                    'bits_per_sample', 'basic_metadata_only'
                ]:
                    extra_data[key] = value
            
            try:
                extra_data_json = json.dumps(extra_data)
            except Exception as e:
                logger.warning(f"Failed to serialize extra data to JSON: {str(e)}")
                extra_data_json = "{}"
            
            logger.debug("Checking if file already exists in database")
            
            # Check if file already exists in database
            cursor.execute('SELECT id, last_modified, duration FROM files WHERE file_path = ?', (file_path,))
            result = cursor.fetchone()
            
            if result:
                # Update existing record if file has been modified or if we're upgrading from basic to full metadata
                file_id, stored_last_modified, stored_duration = result
                
                # Update if:
                # 1. File has been modified since last scan, OR
                # 2. Current metadata has audio info (duration > 0) but stored record doesn't, OR
                # 3. Current metadata is complete but the stored record has only basic info
                if (last_modified > stored_last_modified or 
                    (duration > 0 and stored_duration == 0) or 
                    (not basic_metadata_only and stored_duration == 0)):
                    
                    logger.debug(f"Updating existing record for {file_path}")
                    
                    cursor.execute('''
                    UPDATE files SET
                        filename = ?,
                        format = ?,
                        duration = ?,
                        bitrate = ?,
                        sample_rate = ?,
                        channels = ?,
                        artist = ?,
                        title = ?,
                        album = ?,
                        year = ?,
                        genre = ?,
                        artist_from_filename = ?,
                        title_from_filename = ?,
                        bits_per_sample = ?,
                        last_modified = ?,
                        last_scanned = ?,
                        extra_data = ?
                    WHERE id = ?
                    ''', (
                        filename, format_type, duration, bitrate, sample_rate, 
                        channels, artist, title, album, year, genre,
                        artist_from_filename, title_from_filename, bits_per_sample,
                        last_modified, last_scanned, extra_data_json, file_id
                    ))
                else:
                    logger.debug(f"File hasn't been modified and already has full metadata, skipping update for {file_path}")
            else:
                # Insert new record
                logger.debug(f"Inserting new record for {file_path}")
                
                cursor.execute('''
                INSERT INTO files (
                    file_path, filename, format, duration, bitrate, sample_rate,
                    channels, artist, title, album, year, genre,
                    artist_from_filename, title_from_filename, bits_per_sample,
                    last_modified, last_scanned, extra_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_path, filename, format_type, duration, bitrate, sample_rate,
                    channels, artist, title, album, year, genre,
                    artist_from_filename, title_from_filename, bits_per_sample,
                    last_modified, last_scanned, extra_data_json
                ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Successfully cached metadata for {file_path}")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"SQLite error caching metadata for {metadata.get('file_path', 'unknown')}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error caching metadata for {metadata.get('file_path', 'unknown')}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def cache_multiple_files(self, metadata_list, show_progress=True):
        """
        Cache metadata for multiple audio files.
        
        Args:
            metadata_list (list): List of metadata dictionaries
            show_progress (bool): Whether to show progress bar
        
        Returns:
            int: Number of files successfully cached
        """
        success_count = 0
        
        if show_progress:
            progress_bar = tqdm(total=len(metadata_list), desc="Caching metadata", unit="file")
        
        for i, metadata in enumerate(metadata_list):
            try:
                logger.debug(f"Processing file {i+1}/{len(metadata_list)}")
                if self.cache_file_metadata(metadata):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error processing file {i+1}: {str(e)}")
            
            if show_progress:
                progress_bar.update(1)
        
        if show_progress:
            progress_bar.close()
        
        logger.info(f"Successfully cached metadata for {success_count} of {len(metadata_list)} files")
        return success_count
    
    def get_file_metadata(self, file_path):
        """
        Get metadata for a specific file from cache.
        
        Args:
            file_path (str): Path to the file
        
        Returns:
            dict: Metadata for the file or None if not found
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            conn.row_factory = sqlite3.Row  # Enable dictionary access for rows
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM files WHERE file_path = ?', (file_path,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dictionary
            metadata = dict(row)
            
            # Parse extra_data JSON
            if 'extra_data' in metadata and metadata['extra_data']:
                try:
                    extra_data = json.loads(metadata['extra_data'])
                    metadata.update(extra_data)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse extra_data JSON for {file_path}")
            
            # Remove extra_data field to avoid duplication
            if 'extra_data' in metadata:
                del metadata['extra_data']
            
            conn.close()
            return metadata
        
        except sqlite3.Error as e:
            logger.error(f"Error retrieving metadata for {file_path}: {str(e)}")
            return None
    
    def search_files(self, query=None, artist=None, title=None, album=None, format_type=None, limit=100):
        """
        Search for files matching specified criteria.
        
        Args:
            query (str): General search query (searches across artist, title, album)
            artist (str): Artist name to match
            title (str): Title to match
            album (str): Album to match
            format_type (str): File format to match
            limit (int): Maximum number of results to return
        
        Returns:
            list: List of matching file metadata
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if query:
                # Search across multiple fields
                query_param = f"%{query}%"
                conditions.append("(artist LIKE ? OR title LIKE ? OR album LIKE ? OR filename LIKE ?)")
                params.extend([query_param, query_param, query_param, query_param])
            
            if artist:
                conditions.append("artist LIKE ?")
                params.append(f"%{artist}%")
            
            if title:
                conditions.append("title LIKE ?")
                params.append(f"%{title}%")
            
            if album:
                conditions.append("album LIKE ?")
                params.append(f"%{album}%")
            
            if format_type:
                conditions.append("format = ?")
                params.append(format_type)
            
            sql = "SELECT * FROM files"
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            sql += " ORDER BY artist, album, title LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Convert row to dictionary
                metadata = dict(row)
                
                # Parse extra_data JSON
                if 'extra_data' in metadata and metadata['extra_data']:
                    try:
                        extra_data = json.loads(metadata['extra_data'])
                        metadata.update(extra_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse extra_data JSON for {metadata.get('file_path', 'unknown')}")
                
                # Remove extra_data field to avoid duplication
                if 'extra_data' in metadata:
                    del metadata['extra_data']
                
                results.append(metadata)
            
            conn.close()
            return results
        
        except sqlite3.Error as e:
            logger.error(f"Error searching files: {str(e)}")
            return []
    
    def get_all_files(self, limit=None):
        """
        Get metadata for all files in the cache.
        
        Args:
            limit (int): Maximum number of results to return
        
        Returns:
            list: List of all file metadata
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if limit:
                cursor.execute('SELECT * FROM files LIMIT ?', (limit,))
            else:
                cursor.execute('SELECT * FROM files')
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Convert row to dictionary
                metadata = dict(row)
                
                # Parse extra_data JSON
                if 'extra_data' in metadata and metadata['extra_data']:
                    try:
                        extra_data = json.loads(metadata['extra_data'])
                        metadata.update(extra_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse extra_data JSON for {metadata.get('file_path', 'unknown')}")
                
                # Remove extra_data field to avoid duplication
                if 'extra_data' in metadata:
                    del metadata['extra_data']
                
                results.append(metadata)
            
            conn.close()
            return results
        
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all files: {str(e)}")
            return []
    
    def remove_file(self, file_path):
        """
        Remove a file from the cache.
        
        Args:
            file_path (str): Path to the file to remove
        
        Returns:
            bool: True if file was removed, False otherwise
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM files WHERE file_path = ?', (file_path,))
            conn.commit()
            
            removed = cursor.rowcount > 0
            conn.close()
            
            if removed:
                logger.info(f"Removed file from cache: {file_path}")
            
            return removed
        
        except sqlite3.Error as e:
            logger.error(f"Error removing file from cache: {str(e)}")
            return False
    
    def clear_cache(self):
        """
        Clear all cached file metadata.
        
        Returns:
            bool: True if cache was cleared successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM files')
            conn.commit()
            conn.close()
            
            logger.info("Cache cleared successfully")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def clean_missing_files(self, show_progress=True):
        """
        Remove metadata for files that no longer exist.
        
        Args:
            show_progress (bool): Whether to show progress bar
        
        Returns:
            int: Number of files removed from cache
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            
            # Get all file paths
            cursor.execute('SELECT file_path FROM files')
            rows = cursor.fetchall()
            
            removed_count = 0
            
            if show_progress:
                progress_bar = tqdm(total=len(rows), desc="Cleaning cache", unit="file")
            
            for row in rows:
                file_path = row[0]
                
                if not os.path.exists(file_path):
                    cursor.execute('DELETE FROM files WHERE file_path = ?', (file_path,))
                    removed_count += 1
                
                if show_progress:
                    progress_bar.update(1)
            
            conn.commit()
            conn.close()
            
            if show_progress:
                progress_bar.close()
            
            logger.info(f"Removed {removed_count} missing files from cache")
            return removed_count
        
        except sqlite3.Error as e:
            logger.error(f"Error cleaning missing files from cache: {str(e)}")
            return 0
    
    def get_cache_stats(self):
        """
        Get statistics about the cache.
        
        Returns:
            dict: Cache statistics
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            
            # Get total number of files
            cursor.execute('SELECT COUNT(*) FROM files')
            total_files = cursor.fetchone()[0]
            
            # Get total duration
            cursor.execute('SELECT SUM(duration) FROM files')
            total_duration = cursor.fetchone()[0] or 0
            
            # Get formats
            cursor.execute('SELECT format, COUNT(*) FROM files GROUP BY format')
            formats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get average bitrate
            cursor.execute('SELECT AVG(bitrate) FROM files')
            avg_bitrate = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Calculate total duration in hours
            total_hours = total_duration / 3600
            
            return {
                'total_files': total_files,
                'total_duration': total_duration,
                'total_hours': total_hours,
                'formats': formats,
                'avg_bitrate': avg_bitrate
            }
        
        except sqlite3.Error as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                'total_files': 0,
                'total_duration': 0,
                'total_hours': 0,
                'formats': {},
                'avg_bitrate': 0
            }
            
    def get_candidate_files(self, artist_words=None, title_words=None, limit=1000):
        """
        Get candidate files using fast SQL filtering before fuzzy matching.
        
        Args:
            artist_words (list): List of words from artist name
            title_words (list): List of words from title
            limit (int): Maximum number of candidates to return
        
        Returns:
            list: List of candidate file metadata
        """
        try:
            conn = sqlite3.connect(self.cache_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            # Add conditions for artist words
            if artist_words:
                for word in artist_words:
                    if len(word) >= 2:  # Skip very short words
                        word_pattern = f"%{word}%"
                        conditions.append("(LOWER(artist) LIKE LOWER(?) OR LOWER(filename) LIKE LOWER(?))")
                        params.extend([word_pattern, word_pattern])
            
            # Add conditions for title words
            if title_words:
                for word in title_words:
                    if len(word) >= 2:  # Skip very short words
                        word_pattern = f"%{word}%"
                        conditions.append("(LOWER(title) LIKE LOWER(?) OR LOWER(filename) LIKE LOWER(?))")
                        params.extend([word_pattern, word_pattern])
            
            if not conditions:
                # Fallback to all files if no conditions
                return self.get_all_files(limit)
            
            # Combine conditions with OR (at least one word must match)
            sql = f"SELECT * FROM files WHERE {' OR '.join(conditions)} LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Convert row to dictionary
                metadata = dict(row)
                
                # Parse extra_data JSON
                if 'extra_data' in metadata and metadata['extra_data']:
                    try:
                        extra_data = json.loads(metadata['extra_data'])
                        metadata.update(extra_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse extra_data JSON for {metadata.get('file_path', 'unknown')}")
                
                # Remove extra_data field to avoid duplication
                if 'extra_data' in metadata:
                    del metadata['extra_data']
                
                results.append(metadata)
            
            conn.close()
            
            logger.debug(f"Pre-filtering found {len(results)} candidates from {artist_words} + {title_words}")
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Error getting candidate files: {str(e)}")
            return []