"""
Metadata extractor for audio files using mutagen library.
"""
import os
import re
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.wave import WAVE

from ..utils.logger import get_logger
logger = get_logger()


class MetadataExtractor:
    """Extracts metadata from audio files."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.formats = {
            "mp3": self._extract_mp3_metadata,
            "flac": self._extract_flac_metadata,
            "m4a": self._extract_m4a_metadata,
            "aac": self._extract_m4a_metadata,  # AAC often uses same container as M4A
            "wav": self._extract_wav_metadata
        }
        logger.info("Metadata extractor initialized")
    
    def _get_file_extension(self, file_path):
        """Get the file extension."""
        return os.path.splitext(file_path)[1].lower().lstrip('.')
    
    def _parse_filename(self, filename):
        """
        Parse artist and title from filename based on various formats.
        
        Supported formats:
        - "Artist - Song"
        - "Artist_-_Song"
        - "Artist_Song"
        - "01 - Artist - Song"
        - "01_-_Artist_-_Song"
        - "Song - Artist"
        - "Song_-_Artist"
        - "Song_Artist"
        - "01 - Song - Artist"
        - "01_-_Song_-_Artist"
        
        Returns:
            tuple: (artist, title) or (None, None) if pattern not recognized
        """
        # Remove file extension
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Define patterns with named groups
        patterns = [
            # "Artist - Song" format
            r'^(?P<artist>.+?)\s*-\s*(?P<title>.+)$',
            
            # "Artist_-_Song" format
            r'^(?P<artist>.+?)_-_(?P<title>.+)$',
            
            # "Artist_Song" format
            r'^(?P<artist>.+?)_(?P<title>.+)$',
            
            # "01 - Artist - Song" format
            r'^(?:\d+)\s*-\s*(?P<artist>.+?)\s*-\s*(?P<title>.+)$',
            
            # "01_-_Artist_-_Song" format
            r'^(?:\d+)_-_(?P<artist>.+?)_-_(?P<title>.+)$',
            
            # "Song - Artist" format (reversed)
            r'^(?P<title>.+?)\s*-\s*(?P<artist>.+)$',
            
            # "Song_-_Artist" format (reversed)
            r'^(?P<title>.+?)_-_(?P<artist>.+)$',
            
            # "Song_Artist" format (reversed)
            r'^(?P<title>.+?)_(?P<artist>.+)$',
            
            # "01 - Song - Artist" format (reversed)
            r'^(?:\d+)\s*-\s*(?P<title>.+?)\s*-\s*(?P<artist>.+)$',
            
            # "01_-_Song_-_Artist" format (reversed)
            r'^(?:\d+)_-_(?P<title>.+?)_-_(?P<artist>.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, base_name)
            if match:
                artist = match.group('artist').strip()
                title = match.group('title').strip()
                return artist, title
        
        # If no pattern matches, return filename as title
        return None, base_name
    
    def _extract_mp3_metadata(self, file_path):
        """Extract metadata from MP3 file."""
        try:
            audio = MP3(file_path)
            metadata = {
                'format': 'mp3',
                'duration': audio.info.length,
                'bitrate': audio.info.bitrate // 1000,  # Convert to kbps
                'sample_rate': audio.info.sample_rate,
                'channels': getattr(audio.info, 'channels', None)
            }
            
            # Get ID3 tags if available
            if audio.tags:
                if 'TPE1' in audio.tags:  # Artist
                    metadata['artist'] = str(audio.tags['TPE1'])
                if 'TIT2' in audio.tags:  # Title
                    metadata['title'] = str(audio.tags['TIT2'])
                if 'TALB' in audio.tags:  # Album
                    metadata['album'] = str(audio.tags['TALB'])
                if 'TDRC' in audio.tags:  # Year
                    metadata['year'] = str(audio.tags['TDRC'])
                if 'TCON' in audio.tags:  # Genre
                    metadata['genre'] = str(audio.tags['TCON'])
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting MP3 metadata from {file_path}: {str(e)}")
            return None
    
    def _extract_flac_metadata(self, file_path):
        """Extract metadata from FLAC file."""
        try:
            audio = FLAC(file_path)
            metadata = {
                'format': 'flac',
                'duration': audio.info.length,
                'bitrate': getattr(audio.info, 'bitrate', 0) // 1000,  # Convert to kbps
                'sample_rate': audio.info.sample_rate,
                'channels': audio.info.channels,
                'bits_per_sample': audio.info.bits_per_sample
            }
            
            # Get Vorbis comments
            if audio:
                if 'artist' in audio:
                    metadata['artist'] = audio['artist'][0]
                if 'title' in audio:
                    metadata['title'] = audio['title'][0]
                if 'album' in audio:
                    metadata['album'] = audio['album'][0]
                if 'date' in audio:
                    metadata['year'] = audio['date'][0]
                if 'genre' in audio:
                    metadata['genre'] = audio['genre'][0]
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting FLAC metadata from {file_path}: {str(e)}")
            return None
    
    def _extract_m4a_metadata(self, file_path):
        """Extract metadata from M4A/AAC file."""
        try:
            audio = MP4(file_path)
            metadata = {
                'format': 'm4a' if file_path.lower().endswith('.m4a') else 'aac',
                'duration': audio.info.length,
                'bitrate': audio.info.bitrate // 1000,  # Convert to kbps
                'sample_rate': audio.info.sample_rate,
                'channels': getattr(audio.info, 'channels', None)
            }
            
            # Get iTunes metadata
            if audio.tags:
                if '\xa9ART' in audio.tags:  # Artist
                    metadata['artist'] = audio.tags['\xa9ART'][0]
                if '\xa9nam' in audio.tags:  # Title
                    metadata['title'] = audio.tags['\xa9nam'][0]
                if '\xa9alb' in audio.tags:  # Album
                    metadata['album'] = audio.tags['\xa9alb'][0]
                if '\xa9day' in audio.tags:  # Year
                    metadata['year'] = audio.tags['\xa9day'][0]
                if '\xa9gen' in audio.tags:  # Genre
                    metadata['genre'] = audio.tags['\xa9gen'][0]
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting M4A metadata from {file_path}: {str(e)}")
            return None
    
    def _extract_wav_metadata(self, file_path):
        """Extract metadata from WAV file."""
        try:
            audio = WAVE(file_path)
            metadata = {
                'format': 'wav',
                'duration': audio.info.length,
                'bitrate': getattr(audio.info, 'bitrate', 0) // 1000,  # Convert to kbps
                'sample_rate': audio.info.sample_rate,
                'channels': audio.info.channels
            }
            
            # WAV has limited metadata support
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting WAV metadata from {file_path}: {str(e)}")
            return None
    
    def extract_metadata(self, file_path):
        """
        Extract metadata from audio file.
        
        Args:
            file_path (str): Path to audio file
        
        Returns:
            dict: Metadata extracted from file or None if extraction failed
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        # Get file extension
        ext = self._get_file_extension(file_path)
        if ext not in self.formats:
            logger.warning(f"Unsupported file format: {ext}")
            return None
        
        # Extract metadata based on file format
        metadata = self.formats[ext](file_path)
        
        if metadata:
            # Add filename
            filename = os.path.basename(file_path)
            metadata['filename'] = filename
            metadata['file_path'] = file_path
            
            # Try to parse artist/title from filename if not in metadata
            if 'artist' not in metadata or 'title' not in metadata:
                artist, title = self._parse_filename(filename)
                
                if 'artist' not in metadata and artist:
                    metadata['artist'] = artist
                    metadata['artist_from_filename'] = True
                
                if 'title' not in metadata and title:
                    metadata['title'] = title
                    metadata['title_from_filename'] = True
        
        return metadata

        # Add a new method to the MetadataExtractor class that skips audio analysis
    def extract_basic_metadata(self, file_path):
        """
        Extract only basic metadata from a file without audio analysis.
        This is much faster than full metadata extraction.
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            dict: Basic metadata or None if extraction failed
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            # Get basic file information
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            ext = self._get_file_extension(file_path)
            
            # Create basic metadata
            metadata = {
                'file_path': file_path,
                'filename': filename,
                'format': ext,
                'file_size': file_size,
                # Set default values for audio-specific fields
                'duration': 0,
                'bitrate': 0,
                'sample_rate': 0,
                'channels': 0,
                # Add a flag to indicate this is basic metadata only
                'basic_metadata_only': True
            }
            
            # Try to parse artist/title from filename
            artist, title = self._parse_filename(filename)
            
            if artist:
                metadata['artist'] = artist
                metadata['artist_from_filename'] = True
            
            if title:
                metadata['title'] = title
                metadata['title_from_filename'] = True
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting basic metadata from {file_path}: {str(e)}")
            return None

    def extract_metadata_parallel(self, file_paths, extract_audio_metadata=True, 
                                callback=None, max_workers=None):
        """
        Extract metadata from multiple files using parallel processing.
        
        Args:
            file_paths (list): List of file paths to process
            extract_audio_metadata (bool): Whether to extract audio metadata
            callback (function): Progress callback function
            max_workers (int): Number of parallel workers (None for auto)
        
        Returns:
            list: List of metadata dictionaries
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import multiprocessing
        
        if max_workers is None:
            # Use fewer workers for metadata extraction since it's I/O intensive
            max_workers = min(multiprocessing.cpu_count(), 6)
        
        logger.info(f"Starting parallel metadata extraction with {max_workers} workers")
        logger.info(f"Processing {len(file_paths)} files (audio_metadata={extract_audio_metadata})")
        
        results = []
        processed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self._extract_single_file_metadata, file_path, extract_audio_metadata): file_path 
                for file_path in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                processed_count += 1
                
                try:
                    metadata = future.result()
                    if metadata:
                        results.append(metadata)
                    
                    # Progress callback every 100 files or at the end
                    if callback and (processed_count % 100 == 0 or processed_count == len(file_paths)):
                        progress_percentage = int((processed_count / len(file_paths)) * 100)
                        callback(processed_count, f"Processed {processed_count}/{len(file_paths)} files ({progress_percentage}%)")
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
        
        logger.info(f"Parallel metadata extraction complete: processed {len(results)} files")
        return results

    def _extract_single_file_metadata(self, file_path, extract_audio_metadata=True):
        """
        Extract metadata from a single file (thread-safe version).
        
        Args:
            file_path (str): Path to audio file
            extract_audio_metadata (bool): Whether to extract audio metadata
        
        Returns:
            dict: Metadata dictionary or None if failed
        """
        try:
            return self.extract_metadata(file_path, extract_audio_metadata)
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return None