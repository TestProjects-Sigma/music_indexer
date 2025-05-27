"""
String matcher module for flexible matching of music files.
CLEAN FIXED VERSION - Complete rewrite
"""
from fuzzywuzzy import fuzz
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
        
        # Convert to lowercase first
        text = text.lower()
        
        # Replace common separators with spaces
        text = re.sub(r'[_\-.\(\)\[\]{}]', ' ', text)
        
        # Remove file extensions if present
        text = re.sub(r'\.(mp3|flac|m4a|aac|wav|ogg)$', '', text, flags=re.IGNORECASE)
        
        # Remove common remix/version indicators
        remix_patterns = [
            r'\s*-\s*.*?\s*remix\s*$',
            r'\s*-\s*.*?\s*mix\s*$',
            r'\s*-\s*original\s*mix\s*$',
            r'\s*-\s*radio\s*edit\s*$',
            r'\s*\(.*?\s*remix.*?\)\s*$',
            r'\s*\(.*?\s*mix.*?\)\s*$',
        ]
        
        original_text = text
        for pattern in remix_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # If we removed too much, keep the original
        if len(text.strip()) < len(original_text.strip()) * 0.4:
            text = original_text
        
        # Remove any remaining special characters except spaces and alphanumeric
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
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
        
        # Split into words
        words = cleaned.split()
        
        # Filter out very short words and common words
        stop_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'is', 'are', 'was', 'were'}
        key_words = []
        
        for word in words:
            if len(word) >= 2 and word.lower() not in stop_words:
                key_words.append(word)
        
        return key_words

    def extract_artist_variants(self, artist_text):
        """
        Extract different variants of artist names for better matching.
        
        Args:
            artist_text (str): Original artist text
        
        Returns:
            list: List of artist name variants to try
        """
        if not artist_text:
            return []
        
        variants = [artist_text]  # Include original
        
        # Handle common collaboration separators
        collaboration_separators = [', ', ' & ', ' and ', ' feat. ', ' feat ', ' ft. ', ' ft ', ' vs. ', ' vs ', ' x ']
        
        for sep in collaboration_separators:
            if sep in artist_text.lower():
                # Split and try individual artists
                parts = re.split(re.escape(sep), artist_text, flags=re.IGNORECASE)
                for part in parts:
                    clean_part = part.strip()
                    if clean_part and len(clean_part) > 1:
                        variants.append(clean_part)
                
                # Also try concatenated version
                concat_version = '_and_'.join([p.strip() for p in parts if p.strip()])
                variants.append(concat_version)
                
                # Try with just "and"
                and_version = ' and '.join([p.strip() for p in parts if p.strip()])
                variants.append(and_version)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            variant_lower = variant.lower()
            if variant_lower not in seen:
                seen.add(variant_lower)
                unique_variants.append(variant)
        
        return unique_variants

    def extract_title_variants(self, title_text):
        """
        Extract different variants of titles for better matching.
        
        Args:
            title_text (str): Original title text
        
        Returns:
            list: List of title variants to try
        """
        if not title_text:
            return []
        
        variants = [title_text]  # Include original
        
        # Try without remix/mix information
        base_title = title_text
        
        # Remove remix/mix suffixes
        remix_patterns = [
            r'\s*-\s*.*?\s*remix.*?$',
            r'\s*-\s*.*?\s*mix.*?$', 
            r'\s*-\s*original.*?$',
            r'\s*-\s*radio\s*edit.*?$',
            r'\s*\(.*?\s*remix.*?\).*?$',
            r'\s*\(.*?\s*mix.*?\).*?$',
        ]
        
        for pattern in remix_patterns:
            cleaned = re.sub(pattern, '', base_title, flags=re.IGNORECASE).strip()
            if cleaned and len(cleaned) >= 2:
                variants.append(cleaned)
        
        # Remove duplicates
        seen = set()
        unique_variants = []
        for variant in variants:
            variant_lower = variant.lower()
            if variant_lower not in seen:
                seen.add(variant_lower)
                unique_variants.append(variant)
        
        return unique_variants
   
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
        
        # For very short strings, be more conservative
        if len(clean_str1) <= 2 or len(clean_str2) <= 2:
            if clean_str1 == clean_str2:
                return 100
            else:
                return 0
        
        # Calculate similarity scores using different algorithms
        ratio = fuzz.ratio(clean_str1, clean_str2)
        partial_ratio = fuzz.partial_ratio(clean_str1, clean_str2)
        token_sort_ratio = fuzz.token_sort_ratio(clean_str1, clean_str2)
        
        # Be careful with token_set_ratio - avoid single character matches
        tokens1 = set(clean_str1.split())
        tokens2 = set(clean_str2.split())
        
        if (len(tokens1) > 1 and len(tokens2) > 1 and 
            all(len(token) >= 2 for token in tokens1) and 
            all(len(token) >= 2 for token in tokens2)):
            token_set_ratio = fuzz.token_set_ratio(clean_str1, clean_str2)
        else:
            token_set_ratio = 0
        
        # Check for meaningful containment
        containment_score = 0
        if len(clean_str1) >= 3 and len(clean_str2) >= 3:
            if clean_str1 in clean_str2 or clean_str2 in clean_str1:
                shorter_len = min(len(clean_str1), len(clean_str2))
                longer_len = max(len(clean_str1), len(clean_str2))
                
                if shorter_len / longer_len >= 0.3:
                    containment_score = 85
        
        # Use the highest score among valid methods
        score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio, containment_score)
        
        return score
    
    def match_against_filename(self, query, filename):
        """
        Match query against filename with special handling for filename patterns.
        
        Args:
            query (str): Search query
            filename (str): Filename to match against
        
        Returns:
            int: Match score (0-100)
        """
        if not query or not filename:
            return 0
        
        # Basic string matching using fuzzy algorithms
        basic_score = self.match_strings(query, filename)
        
        # Check for meaningful substring matches
        clean_query = self.clean_string(query)
        clean_filename = self.clean_string(filename)
        
        if clean_query and clean_filename and len(clean_query) >= 3:
            if clean_query in clean_filename:
                query_length = len(clean_query)
                filename_length = len(clean_filename)
                
                if query_length >= 4:
                    coverage = query_length / filename_length
                    
                    if coverage >= 0.15:
                        substring_score = min(85, int(70 + coverage * 30))
                        basic_score = max(basic_score, substring_score)
                    elif coverage >= 0.05:
                        substring_score = min(75, int(60 + coverage * 50))
                        basic_score = max(basic_score, substring_score)
        
        return basic_score
    
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
        filename_score = 0
        
        # Get metadata fields
        file_artist = file_metadata.get('artist', '')
        file_title = file_metadata.get('title', '')
        filename = file_metadata.get('filename', '')
        
        # Match artist if provided - try multiple variants
        if query_artist and len(query_artist.strip()) >= 2:
            artist_variants = self.extract_artist_variants(query_artist)
            
            # Try matching against metadata artist
            if file_artist:
                for variant in artist_variants:
                    variant_score = self.match_strings(variant, file_artist)
                    artist_score = max(artist_score, variant_score)
            
            # Also try matching against filename if score is still low
            if artist_score < self.threshold and filename:
                for variant in artist_variants:
                    filename_artist_score = self.match_against_filename(variant, filename)
                    artist_score = max(artist_score, filename_artist_score)
        
        # Match title if provided - try multiple variants
        if query_title and len(query_title.strip()) >= 2:
            title_variants = self.extract_title_variants(query_title)
            
            # Try matching against metadata title
            if file_title:
                for variant in title_variants:
                    variant_score = self.match_strings(variant, file_title)
                    title_score = max(title_score, variant_score)
            
            # Also try matching against filename if score is still low
            if title_score < self.threshold and filename:
                for variant in title_variants:
                    filename_title_score = self.match_against_filename(variant, filename)
                    title_score = max(title_score, filename_title_score)
        
        # Combined filename matching with variants
        if filename and (query_artist or query_title):
            combined_variants = []
            
            if query_artist:
                artist_variants = self.extract_artist_variants(query_artist)
                artist_variants.sort(key=len)
                combined_variants.extend(artist_variants[:2])
            
            if query_title:
                title_variants = self.extract_title_variants(query_title)
                title_variants.sort(key=len)
                combined_variants.extend(title_variants[:2])
            
            if combined_variants:
                for variant in combined_variants:
                    if len(variant) >= 3:
                        variant_filename_score = self.match_against_filename(variant, filename)
                        filename_score = max(filename_score, variant_filename_score)
        
        # Calculate combined score with flexible logic for collaborations
        if query_artist and query_title and len(query_artist.strip()) >= 2 and len(query_title.strip()) >= 2:
            # Both artist and title provided
            
            # Be more lenient if we detect this might be a collaboration
            is_collaboration = any(sep in query_artist.lower() for sep in [', ', ' & ', ' and ', ' feat', ' ft', ' vs', ' x '])
            
            if is_collaboration:
                min_required_score = max(50, self.threshold - 25)
            else:
                min_required_score = max(60, self.threshold - 15)
            
            if artist_score >= min_required_score and title_score >= min_required_score:
                combined_score = (artist_score + title_score) / 2
            elif artist_score >= self.threshold:
                weight = 0.8 if is_collaboration else 0.7
                combined_score = artist_score * weight + title_score * (1 - weight)
            elif title_score >= self.threshold:
                weight = 0.8 if is_collaboration else 0.7
                combined_score = title_score * weight + artist_score * (1 - weight)
            elif filename_score >= (self.threshold + 5):
                combined_score = filename_score * 0.7
            else:
                combined_score = max(artist_score, title_score, filename_score) * 0.5
                
        elif query_artist and len(query_artist.strip()) >= 2:
            combined_score = max(artist_score, filename_score * 0.9)
        elif query_title and len(query_title.strip()) >= 2:
            combined_score = max(title_score, filename_score * 0.9)
        else:
            combined_score = 0
        
        # Reduce penalty for score differences in collaborations
        if (query_artist and query_title and 
            len(query_artist.strip()) >= 2 and len(query_title.strip()) >= 2):
            
            is_collaboration = any(sep in query_artist.lower() for sep in [', ', ' & ', ' and ', ' feat', ' ft', ' vs', ' x '])
            
            if not is_collaboration:
                score_diff = abs(artist_score - title_score)
                if score_diff > 40:
                    combined_score *= 0.85
        
        # Check if match exceeds threshold
        is_match = combined_score >= self.threshold
        
        return {
            'file_path': file_metadata.get('file_path', ''),
            'artist': file_artist,
            'title': file_title,
            'filename': filename,
            'artist_score': artist_score,
            'title_score': title_score,
            'filename_score': filename_score,
            'combined_score': combined_score,
            'is_match': is_match
        }
    
    def find_matches(self, query_artist, query_title, file_metadata_list):
        """
        Find matches for a song query in a list of file metadata.
        
        Args:
            query_artist (str): Artist to match
            query_title (str): Title to match
            file_metadata_list (list): List of file metadata dictionaries
        
        Returns:
            list: List of match results, sorted by score
        """
        matches = []
        
        logger.debug(f"Searching for artist='{query_artist}', title='{query_title}' in {len(file_metadata_list)} files")
        
        for metadata in file_metadata_list:
            match_result = self.match_song(query_artist, query_title, metadata)
            
            if match_result['is_match']:
                # Add full metadata to match result
                match_result.update(metadata)
                matches.append(match_result)
        
        # Sort matches by combined score (descending)
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Limit results to top 50
        limited_matches = matches[:50]
        
        logger.debug(f"Found {len(matches)} matches (showing top {len(limited_matches)})")
        return limited_matches