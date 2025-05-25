"""
String matcher module for flexible matching of music files.
"""
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re

from ..utils.logger import get_logger
logger = get_logger()


class StringMatcher:
    """
    Provides string matching functionality for music files.
    """
    
    def __init__(self, threshold=75):
        """
        Initialize the string matcher with specified threshold.
        
        Args:
            threshold (int): Similarity threshold (0-100) for fuzzy matching
        """
        self.threshold = threshold
        logger.info(f"String matcher initialized with threshold {threshold}")
    
    def set_threshold(self, threshold):
        """
        Set the similarity threshold.
        
        Args:
            threshold (int): New similarity threshold (0-100)
        """
        self.threshold = max(0, min(100, threshold))
        logger.info(f"String matcher threshold set to {self.threshold}")
    
    def clean_string(self, text):
        """
        Clean a string by removing special characters and normalizing whitespace.
        
        Args:
            text (str): String to clean
        
        Returns:
            str: Cleaned string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace special characters with space
        text = re.sub(r'[_\-.]', ' ', text)
        
        # Remove any non-alphanumeric characters (except spaces)
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace (replace multiple spaces with single space)
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text

    def extract_key_words(self, text):
        """
        Extract key words from text for pre-filtering.
        
        Args:
            text (str): Text to extract words from
        
        Returns:
            list: List of cleaned key words
        """
        if not text:
            return []
        
        # Clean the text
        cleaned = self.clean_string(text)
        
        # Split into words and filter
        words = cleaned.split()
        
        # Filter out very short words and common words
        stop_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an'}
        key_words = []
        
        for word in words:
            if len(word) >= 2 and word.lower() not in stop_words:
                key_words.append(word)
        
        return key_words
   
    def match_strings(self, str1, str2):
        """
        Match two strings and return similarity score.
        
        Args:
            str1 (str): First string
            str2 (str): Second string
        
        Returns:
            int: Similarity score (0-100)
        """
        if not str1 or not str2:
            return 0
        
        # Clean strings
        clean_str1 = self.clean_string(str1)
        clean_str2 = self.clean_string(str2)
        
        if not clean_str1 or not clean_str2:
            return 0
        
        # Calculate similarity scores using different algorithms
        ratio = fuzz.ratio(clean_str1, clean_str2)
        partial_ratio = fuzz.partial_ratio(clean_str1, clean_str2)
        token_sort_ratio = fuzz.token_sort_ratio(clean_str1, clean_str2)
        token_set_ratio = fuzz.token_set_ratio(clean_str1, clean_str2)
        
        # Use the highest score
        score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)
        
        return score
    
    def is_match(self, str1, str2):
        """
        Check if two strings match based on threshold.
        
        Args:
            str1 (str): First string
            str2 (str): Second string
        
        Returns:
            bool: True if strings match, False otherwise
        """
        score = self.match_strings(str1, str2)
        return score >= self.threshold
    
    def match_song(self, query_artist, query_title, file_metadata):
        """
        Match a song query against file metadata.
        
        Args:
            query_artist (str): Artist to match
            query_title (str): Title to match
            file_metadata (dict): File metadata dictionary
        
        Returns:
            dict: Match result with scores
        """
        artist_score = 0
        title_score = 0
        
        # Get artist and title from metadata
        file_artist = file_metadata.get('artist', '')
        file_title = file_metadata.get('title', '')
        
        # Match artist if provided
        if query_artist and file_artist:
            artist_score = self.match_strings(query_artist, file_artist)
        
        # Match title if provided
        if query_title and file_title:
            title_score = self.match_strings(query_title, file_title)
        
        # Calculate combined score
        # If both artist and title are provided, use weighted average
        if query_artist and query_title:
            combined_score = (artist_score + title_score) / 2
        # If only one is provided, use that score
        elif query_artist:
            combined_score = artist_score
        elif query_title:
            combined_score = title_score
        else:
            combined_score = 0
        
        # Check if match exceeds threshold
        is_match = combined_score >= self.threshold
        
        return {
            'file_path': file_metadata.get('file_path', ''),
            'artist': file_artist,
            'title': file_title,
            'artist_score': artist_score,
            'title_score': title_score,
            'combined_score': combined_score,
            'is_match': is_match
        }
    
    def find_matches(self, query_artist, query_title, file_metadata_list):
        """
        Find matches for a song query in a list of file metadata.
        Uses pre-filtering for better performance with large collections.
        
        Args:
            query_artist (str): Artist to match
            query_title (str): Title to match
            file_metadata_list (list): List of file metadata dictionaries
        
        Returns:
            list: List of match results, sorted by score
        """
        # If we have a small list, use the old method
        if len(file_metadata_list) < 5000:
            return self._find_matches_original(query_artist, query_title, file_metadata_list)
        
        # For large lists, we should use pre-filtering
        # This method is called with the full file list, so we'll still process all
        # but we'll add early termination for better performance
        matches = []
        excellent_matches = []  # Matches with score >= 95
        
        for metadata in file_metadata_list:
            match_result = self.match_song(query_artist, query_title, metadata)
            
            if match_result['is_match']:
                # Add full metadata to match result
                match_result.update(metadata)
                
                if match_result['combined_score'] >= 95:
                    excellent_matches.append(match_result)
                    # If we found 3 excellent matches, we probably have what we need
                    if len(excellent_matches) >= 3:
                        matches.extend(excellent_matches)
                        break
                else:
                    matches.append(match_result)
        
        # If we didn't find excellent matches, use all matches
        if len(excellent_matches) < 3:
            matches.extend(excellent_matches)
        
        # Sort matches by combined score (descending)
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Limit results to top 20 to avoid overwhelming the UI
        return matches[:20]

    def _find_matches_original(self, query_artist, query_title, file_metadata_list):
        """Original find_matches method for smaller lists."""
        matches = []
        
        for metadata in file_metadata_list:
            match_result = self.match_song(query_artist, query_title, metadata)
            
            if match_result['is_match']:
                # Add full metadata to match result
                match_result.update(metadata)
                matches.append(match_result)
        
        # Sort matches by combined score (descending)
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return matches
    
    def process_match_file(self, match_file_path, file_metadata_list):
        """
        Process a match file with artist and title on each line.
        
        Args:
            match_file_path (str): Path to match file
            file_metadata_list (list): List of file metadata dictionaries
        
        Returns:
            list: List of match results for each line
        """
        results = []
        
        try:
            with open(match_file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue  # Skip empty lines and comments
                    
                    # Try to parse artist and title
                    parts = re.split(r' - ', line, maxsplit=1)
                    
                    if len(parts) == 2:
                        artist, title = parts
                    else:
                        # If no separator found, assume the whole line is the title
                        artist, title = "", line
                    
                    # Find matches
                    matches = self.find_matches(artist, title, file_metadata_list)
                    
                    results.append({
                        'line_num': line_num,
                        'line': line,
                        'artist': artist,
                        'title': title,
                        'matches': matches
                    })
        
        except Exception as e:
            logger.error(f"Error processing match file {match_file_path}: {str(e)}")
        
        return results

def extract_key_words(self, text):
    """
    Extract key words from text for pre-filtering.
    
    Args:
        text (str): Text to extract words from
    
    Returns:
        list: List of cleaned key words
    """
    if not text:
        return []
    
    # Clean the text
    cleaned = self.clean_string(text)
    
    # Split into words and filter
    words = cleaned.split()
    
    # Filter out very short words and common words
    stop_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an'}
    key_words = []
    
    for word in words:
        if len(word) >= 2 and word.lower() not in stop_words:
            key_words.append(word)
    
    return key_words