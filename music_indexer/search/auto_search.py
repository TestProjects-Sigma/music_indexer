"""
Automatic search module for batch processing of music file matches.
"""
import os
import re
from tqdm import tqdm

from ..core.cache_manager import CacheManager
from ..search.string_matcher import StringMatcher
from ..utils.logger import get_logger

logger = get_logger()


class AutoSearch:
    """
    Provides automatic search functionality for music files.
    Processes match files with artist/title pairs for batch matching.
    """
    
    def __init__(self, cache_manager=None, string_matcher=None):
        """
        Initialize automatic search with specified components.
        
        Args:
            cache_manager (CacheManager): Cache manager instance
            string_matcher (StringMatcher): String matcher instance
        """
        self.cache_manager = cache_manager or CacheManager()
        self.string_matcher = string_matcher or StringMatcher()
        logger.info("Automatic search initialized")
    
    def _parse_match_line(self, line):
        """
        Parse a line from a match file.
        
        Args:
            line (str): Line to parse
        
        Returns:
            tuple: (artist, title) or (None, None) if invalid
        """
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            return None, None
        
        # Try to parse artist and title with various separators
        for separator in [' - ', ' – ', ': ', ' : ', '_-_', ',']:
            parts = line.split(separator, 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        # If no separator found, assume the whole line is the title
        return "", line
    
    def _load_match_file(self, file_path):
        """
        Load a match file and extract artist/title pairs.
        
        Args:
            file_path (str): Path to match file
        
        Returns:
            list: List of (line_num, line, artist, title) tuples
        """
        if not os.path.exists(file_path):
            logger.error(f"Match file not found: {file_path}")
            return []
        
        pairs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    artist, title = self._parse_match_line(line)
                    if artist is not None or title:
                        pairs.append((line_num, line, artist, title))
        
        except Exception as e:
            logger.error(f"Error loading match file {file_path}: {str(e)}")
        
        logger.info(f"Loaded {len(pairs)} artist/title pairs from {file_path}")
        return pairs
    
    def _find_matches_for_pair(self, artist, title, all_files):
        """
        Find matches for an artist/title pair in file list.
        
        Args:
            artist (str): Artist to match
            title (str): Title to match
            all_files (list): List of file metadata dictionaries
        
        Returns:
            list: List of matches sorted by score
        """
        return self.string_matcher.find_matches(artist, title, all_files)
    
    def process_match_file(self, file_path, show_progress=True):
        """
        Process a match file and find matches for each entry.
        
        Args:
            file_path (str): Path to match file
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of results for each line
        """
        # Load pairs from match file
        pairs = self._load_match_file(file_path)
        
        if not pairs:
            logger.warning(f"No valid entries found in match file: {file_path}")
            return []
        
        # Get all files from cache
        all_files = self.cache_manager.get_all_files()
        
        if not all_files:
            logger.warning("No files in cache to match against")
            return []
        
        # Process each pair
        results = []
        
        if show_progress:
            progress_bar = tqdm(total=len(pairs), desc="Processing matches", unit="entry")
        
        for line_num, line, artist, title in pairs:
            # Find matches
            matches = self._find_matches_for_pair(artist, title, all_files)
            
            results.append({
                'line_num': line_num,
                'line': line,
                'artist': artist,
                'title': title,
                'matches': matches
            })
            
            if show_progress:
                progress_bar.update(1)
        
        if show_progress:
            progress_bar.close()
        
        logger.info(f"Processed {len(results)} entries from match file")
        return results
    
    def save_results(self, results, output_file):
        """
        Save search results to a file.
        
        Args:
            results (list): List of search results
            output_file (str): Path to output file
        
        Returns:
            bool: True if results were saved successfully, False otherwise
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write("# Automatic Search Results\n")
                file.write("# Format: Line Number, Original Line, Artist, Title, Match Count\n")
                file.write("# Followed by matches (if any) with scores\n\n")
                
                for result in results:
                    line_num = result['line_num']
                    line = result['line']
                    artist = result['artist']
                    title = result['title']
                    matches = result['matches']
                    
                    file.write(f"Line {line_num}: \"{line}\"\n")
                    file.write(f"  Parsed as Artist: \"{artist}\", Title: \"{title}\"\n")
                    file.write(f"  Found {len(matches)} matches:\n")
                    
                    if matches:
                        for i, match in enumerate(matches, 1):
                            file.write(f"    {i}. {match.get('filename', 'Unknown')}\n")
                            file.write(f"       Artist: {match.get('artist', 'Unknown')}, ")
                            file.write(f"Title: {match.get('title', 'Unknown')}\n")
                            file.write(f"       Format: {match.get('format', 'Unknown')}, ")
                            file.write(f"Duration: {match.get('duration', 0):.2f}s, ")
                            file.write(f"Bitrate: {match.get('bitrate', 0)} kbps\n")
                            file.write(f"       Match Score: {match.get('combined_score', 0):.2f}%\n")
                    else:
                        file.write("    No matches found\n")
                    
                    file.write("\n")
            
            logger.info(f"Results saved to {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving results to {output_file}: {str(e)}")
            return False
    
    def set_similarity_threshold(self, threshold):
        """
        Set the similarity threshold for fuzzy matching.
        
        Args:
            threshold (int): New similarity threshold (0-100)
        """
        self.string_matcher.set_threshold(threshold)
