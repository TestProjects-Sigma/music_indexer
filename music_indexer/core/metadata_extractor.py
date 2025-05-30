"""
Fixed metadata extractor for electronic music collections.
Replace your existing metadata_extractor.py with this version.
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
    """Extracts metadata from audio files with electronic music optimizations."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.formats = {
            "mp3": self._extract_mp3_metadata,
            "flac": self._extract_flac_metadata,
            "m4a": self._extract_m4a_metadata,
            "aac": self._extract_m4a_metadata,
            "wav": self._extract_wav_metadata
        }
        
        # Electronic music labels from your collection
        self.known_labels = {
            'dps', 'trt', 'pms', 'sq', 'doc', 'vmc', 'dwm', 'apc', 'rfl', 'mim'
        }
        
        logger.info("Electronic music metadata extractor initialized")
    
    def _get_file_extension(self, file_path):
        """Get the file extension."""
        return os.path.splitext(file_path)[1].lower().lstrip('.')
    
    def _parse_filename(self, filename):
        """
        Parse artist and title from filename - FIXED VERSION.
        Handles all problematic patterns from your electronic music collection.
        
        Args:
            filename (str): Original filename
            
        Returns:
            tuple: (artist, title) properly parsed
        """
        # Remove file extension
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # CRITICAL FIX 1: Remove track numbers and vinyl positions FIRST
        # Patterns: 01-, 02-, a1_, b2_, 101-, etc.
        track_patterns = [
            r'^[a-z]?\d+[-_]\s*',  # a1-, 01-, 101-, a1_, etc.
            r'^\d+\s*[-_]\s*',     # Just numbers: 01-, 02-
        ]
        
        for pattern in track_patterns:
            base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
        
        # CRITICAL FIX 2: Handle the _-_ pattern (74% of your files)
        # Pattern: artist_-_title-label
        underscore_dash_pattern = r'^(.+?)_-_(.+?)(?:-([a-z]{2,4}))?$'
        underscore_dash_match = re.match(underscore_dash_pattern, base_name, re.IGNORECASE)
        if underscore_dash_match:
            raw_artist = underscore_dash_match.group(1)
            raw_title = underscore_dash_match.group(2)
            
            # Clean up the artist (remove trailing underscores)
            artist = re.sub(r'_+$', '', raw_artist).replace('_', ' ').strip()
            
            # Clean up the title (remove leading underscores)
            title = re.sub(r'^_+', '', raw_title).replace('_', ' ').strip()
            
            return artist, title
        
        # CRITICAL FIX 3: Handle standard dash separation
        # Pattern: artist-title-label
        dash_parts = base_name.split('-')
        if len(dash_parts) >= 2:
            artist = dash_parts[0].replace('_', ' ').strip()
            
            # Handle label at the end
            if len(dash_parts) > 2 and dash_parts[-1].lower() in self.known_labels:
                title = '-'.join(dash_parts[1:-1]).replace('_', ' ').strip()
            else:
                title = '-'.join(dash_parts[1:]).replace('_', ' ').strip()
            
            return artist, title
        
        # CRITICAL FIX 4: Handle underscore separation (without _-_)
        if '_' in base_name and '_-_' not in base_name:
            parts = base_name.split('_', 1)  # Split only on first underscore
            artist = parts[0].strip()
            title = parts[1].replace('_', ' ').strip() if len(parts) > 1 else ''
            
            return artist, title
        
        # Fallback - treat as title only
        return None, base_name.replace('_', ' ').strip()
    
    def _extract_mp3_metadata(self, file_path):
        """Extract metadata from MP3 file."""
        try:
            audio = MP3(file_path)
            metadata = {
                'format': 'mp3',
                'duration': audio.info.length,
                'bitrate': audio.info.bitrate // 1000,
                'sample_rate': audio.info.sample_rate,
                'channels': getattr(audio.info, 'channels', None)
            }
            
            if audio.tags:
                if 'TPE1' in audio.tags:
                    metadata['artist'] = str(audio.tags['TPE1'])
                if 'TIT2' in audio.tags:
                    metadata['title'] = str(audio.tags['TIT2'])
                if 'TALB' in audio.tags:
                    metadata['album'] = str(audio.tags['TALB'])
                if 'TDRC' in audio.tags:
                    metadata['year'] = str(audio.tags['TDRC'])
                if 'TCON' in audio.tags:
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
                'bitrate': getattr(audio.info, 'bitrate', 0) // 1000,
                'sample_rate': audio.info.sample_rate,
                'channels': audio.info.channels,
                'bits_per_sample': audio.info.bits_per_sample
            }
            
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
                'bitrate': audio.info.bitrate // 1000,
                'sample_rate': audio.info.sample_rate,
                'channels': getattr(audio.info, 'channels', None)
            }
            
            if audio.tags:
                if '\xa9ART' in audio.tags:
                    metadata['artist'] = audio.tags['\xa9ART'][0]
                if '\xa9nam' in audio.tags:
                    metadata['title'] = audio.tags['\xa9nam'][0]
                if '\xa9alb' in audio.tags:
                    metadata['album'] = audio.tags['\xa9alb'][0]
                if '\xa9day' in audio.tags:
                    metadata['year'] = audio.tags['\xa9day'][0]
                if '\xa9gen' in audio.tags:
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
                'bitrate': getattr(audio.info, 'bitrate', 0) // 1000,
                'sample_rate': audio.info.sample_rate,
                'channels': audio.info.channels
            }
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting WAV metadata from {file_path}: {str(e)}")
            return None
    
    def extract_metadata(self, file_path):
        """
        Extract metadata from audio file - FIXED VERSION.
        
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
            
            # Get metadata fields
            audio_artist = metadata.get('artist', '').strip()
            audio_title = metadata.get('title', '').strip()
            
            # Parse filename using FIXED parser
            filename_artist, filename_title = self._parse_filename(filename)
            
            # CRITICAL FIX: Use proper logic to choose best metadata
            # Check if audio metadata is valid (not just track numbers)
            audio_artist_valid = (audio_artist and 
                                len(audio_artist) > 2 and 
                                not audio_artist.isdigit() and
                                not re.match(r'^[a-z]?\d+$', audio_artist.lower()))
            
            audio_title_valid = (audio_title and len(audio_title) > 2)
            
            # Choose best artist
            if audio_artist_valid:
                metadata['artist'] = audio_artist
                metadata['artist_from_filename'] = False
            elif filename_artist and len(filename_artist) > 1:
                metadata['artist'] = filename_artist
                metadata['artist_from_filename'] = True
            else:
                metadata['artist'] = filename_artist or audio_artist
                metadata['artist_from_filename'] = True
            
            # Choose best title
            if audio_title_valid:
                metadata['title'] = audio_title
                metadata['title_from_filename'] = False
            elif filename_title and len(filename_title) > 1:
                metadata['title'] = filename_title
                metadata['title_from_filename'] = True
            else:
                metadata['title'] = filename_title or audio_title
                metadata['title_from_filename'] = True
        
        return metadata
    
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
                'duration': 0,
                'bitrate': 0,
                'sample_rate': 0,
                'channels': 0,
                'basic_metadata_only': True
            }
            
            # Parse filename using FIXED parser
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
            if extract_audio_metadata:
                return self.extract_metadata(file_path)
            else:
                return self.extract_basic_metadata(file_path)
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return None