"""
FIXED Conservative String Matcher - Eliminates False Positives
Replace your string_matcher.py with this version immediately.
"""
from fuzzywuzzy import fuzz
import re

from ..utils.logger import get_logger
logger = get_logger()


class StringMatcher:
    """
    FIXED Conservative string matcher that eliminates false positives.
    This version is much more strict and accurate.
    """
    
    def __init__(self, threshold=75):
        """
        Initialize the string matcher with specified threshold.
        
        Args:
            threshold (int): Similarity threshold (0-100) for fuzzy matching
        """
        self.threshold = threshold
        
        # Electronic music specific stop words
        self.stop_words = {
            'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'is', 'are',
            'vs', 'feat', 'ft', 'dj', 'mc', 'original', 'mix', 'remix', 'edit',
            'extended', 'radio', 'club', 'dance', 'version', 'remaster', 'remastered'
        }
        
        logger.info(f"FIXED Conservative string matcher initialized with threshold {threshold}")
    
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
        Clean a string for matching - CONSERVATIVE approach.
        
        Args:
            text (str): String to clean
        
        Returns:
            str: Cleaned string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove file extensions
        text = re.sub(r'\.(mp3|flac|m4a|aac|wav|ogg)$', '', text, flags=re.IGNORECASE)
        
        # Replace separators with spaces (but be conservative)
        text = re.sub(r'[_\-.]', ' ', text)
        
        # Remove remix info in parentheses
        text = re.sub(r'\s*\([^)]*(?:remix|mix|edit|remaster|version|original|extended|radio|club)[^)]*\)\s*', ' ', text, flags=re.IGNORECASE)
        
        # Remove leading track numbers
        text = re.sub(r'^\s*[a-z]?\d+\s*', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_meaningful_words(self, text):
        """
        Extract meaningful words from text - CONSERVATIVE filtering.
        
        Args:
            text (str): Input text
            
        Returns:
            list: List of meaningful words
        """
        if not text:
            return []
        
        # Clean and split
        cleaned = self.clean_string(text)
        words = cleaned.split()
        
        # Filter meaningful words STRICTLY
        meaningful_words = []
        for word in words:
            if (len(word) >= 3 and  # At least 3 characters
                word not in self.stop_words and  # Not a stop word
                not word.isdigit() and  # Not just a number
                len(word) <= 20):  # Not too long (likely garbage)
                meaningful_words.append(word)
        
        return meaningful_words
    
    def calculate_word_overlap_score(self, search_words, target_words):
        """
        Calculate score based on meaningful word overlap - CONSERVATIVE.
        
        Args:
            search_words (list): Words from search term
            target_words (list): Words from target text
        
        Returns:
            int: Match score (0-100)
        """
        if not search_words or not target_words:
            return 0
        
        search_set = set(word.lower() for word in search_words)
        target_set = set(word.lower() for word in target_words)
        
        # Calculate overlap
        common_words = search_set & target_set
        
        if not common_words:
            return 0
        
        # STRICT requirements:
        search_coverage = len(common_words) / len(search_set)
        target_coverage = len(common_words) / len(target_set)
        
        # Require good coverage on BOTH sides
        if search_coverage < 0.6:  # At least 60% of search words must match
            return 0
        
        # Calculate conservative score
        score = (search_coverage + target_coverage) / 2 * 100
        
        # Apply penalty for low absolute word count
        if len(common_words) == 1 and len(search_set) > 1:
            score *= 0.7  # Penalty for single word matches
        
        return min(90, int(score))  # Cap at 90% for word overlap
    
    def match_strings(self, str1, str2):
        """
        Match two strings using CONSERVATIVE approach.
        
        Args:
            str1 (str): First string (search term)
            str2 (str): Second string (target)
        
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
        
        # Strategy 1: Word overlap (primary method)
        search_words = self.extract_meaningful_words(clean_str1)
        target_words = self.extract_meaningful_words(clean_str2)
        
        word_score = self.calculate_word_overlap_score(search_words, target_words)
        
        # Strategy 2: Fuzzy matching (secondary, with strict limits)
        fuzzy_score = 0
        if len(clean_str1) >= 3 and len(clean_str2) >= 3:
            # Use only the most conservative fuzzy method
            ratio = fuzz.ratio(clean_str1, clean_str2)
            partial_ratio = fuzz.partial_ratio(clean_str1, clean_str2)
            
            # Be VERY careful with token_set_ratio - it causes false positives
            # Only use it if both strings have multiple meaningful words
            if len(search_words) >= 2 and len(target_words) >= 2:
                token_sort = fuzz.token_sort_ratio(clean_str1, clean_str2)
                fuzzy_score = max(ratio, partial_ratio, token_sort)
            else:
                fuzzy_score = max(ratio, partial_ratio)
            
            # Apply strict penalty to fuzzy scores
            fuzzy_score = int(fuzzy_score * 0.85)  # 15% penalty for fuzzy vs exact
        
        # Use the BETTER of the two methods, but apply strict validation
        best_score = max(word_score, fuzzy_score)
        
        # CRITICAL: Apply additional validation
        if best_score > 0:
            # Ensure there's actually meaningful similarity
            if not search_words or not target_words:
                return 0
            
            # If score is suspiciously high, validate it
            if best_score >= 90:
                common_words = set(search_words) & set(target_words)
                if len(common_words) == 0:
                    return 0  # No common words = no high score
                
                # Check for single character false positives
                if len(common_words) == 1 and len(list(common_words)[0]) <= 2:
                    return max(50, best_score * 0.6)  # Heavy penalty
        
        return best_score
    
    def match_against_filename(self, query, filename):
        """
        Match query against filename with CONSERVATIVE approach.
        
        Args:
            query (str): Search query
            filename (str): Filename to match against
        
        Returns:
            int: Match score (0-100)
        """
        if not query or not filename:
            return 0
        
        # Clean the filename
        clean_filename = self.clean_string(filename)
        clean_query = self.clean_string(query)
        
        # Try normal string matching first
        normal_score = self.match_strings(clean_query, clean_filename)
        
        # If we got a good score, return it
        if normal_score >= 80:
            return normal_score
        
        # Try matching against filename parts
        filename_parts = re.split(r'\s*-\s*', clean_filename)
        
        best_part_score = 0
        for part in filename_parts:
            if len(part.strip()) >= 3:  # Skip very short parts
                part_score = self.match_strings(clean_query, part.strip())
                best_part_score = max(best_part_score, part_score)
        
        # Return the better score, but apply conservative limits
        final_score = max(normal_score, best_part_score)
        
        # Additional filename-specific validation
        if final_score >= 85:
            # Ensure the match makes sense for a filename
            query_words = set(self.extract_meaningful_words(clean_query))
            filename_words = set(self.extract_meaningful_words(clean_filename))
            
            if query_words and filename_words:
                overlap = len(query_words & filename_words) / len(query_words)
                if overlap < 0.4:  # Less than 40% word overlap
                    final_score = min(75, final_score)  # Reduce suspicious high scores
        
        return final_score
    
    def match_song(self, query_artist, query_title, file_metadata):
        """
        Match a song query against file metadata with STRICT validation.
        
        Args:
            query_artist (str): Artist to match
            query_title (str): Title to match
            file_metadata (dict): File metadata dictionary
        
        Returns:
            dict: Match result with scores
        """
        # Get metadata fields
        file_artist = file_metadata.get('artist', '')
        file_title = file_metadata.get('title', '')
        filename = file_metadata.get('filename', '')
        
        artist_score = 0
        title_score = 0
        filename_score = 0
        
        # Clean inputs
        clean_query_artist = self.clean_string(query_artist)
        clean_query_title = self.clean_string(query_title)
        clean_file_artist = self.clean_string(file_artist)
        clean_file_title = self.clean_string(file_title)
        
        # Match artist if provided
        if clean_query_artist and len(clean_query_artist) >= 2:
            if clean_file_artist:
                artist_score = self.match_strings(clean_query_artist, clean_file_artist)
            
            # Try against filename if metadata match is weak
            if artist_score < 70 and filename:
                filename_artist_score = self.match_against_filename(clean_query_artist, filename)
                artist_score = max(artist_score, filename_artist_score)
        
        # Match title if provided
        if clean_query_title and len(clean_query_title) >= 2:
            if clean_file_title:
                title_score = self.match_strings(clean_query_title, clean_file_title)
            
            # Try against filename if metadata match is weak
            if title_score < 70 and filename:
                filename_title_score = self.match_against_filename(clean_query_title, filename)
                title_score = max(title_score, filename_title_score)
        
        # Calculate combined score with STRICT requirements
        combined_score = 0
        
        if clean_query_artist and clean_query_title:
            # Both artist and title provided - STRICT requirements
            min_threshold = max(65, self.threshold - 10)
            
            if artist_score >= min_threshold and title_score >= min_threshold:
                # Both match reasonably well
                combined_score = (artist_score * 0.6 + title_score * 0.4)
            elif artist_score >= 85 or title_score >= 85:
                # One very strong match might be acceptable
                combined_score = max(artist_score, title_score) * 0.75
            else:
                # Try filename matching as last resort
                if filename:
                    full_query = f"{clean_query_artist} {clean_query_title}".strip()
                    filename_score = self.match_against_filename(full_query, filename)
                    if filename_score >= 80:
                        combined_score = filename_score * 0.65
        
        elif clean_query_artist:
            # Only artist provided
            combined_score = artist_score
        elif clean_query_title:
            # Only title provided
            combined_score = title_score
        
        # FINAL VALIDATION - eliminate suspicious high scores
        if combined_score >= 95:
            # Very high scores need additional validation
            query_words = set(self.extract_meaningful_words(f"{query_artist} {query_title}"))
            file_words = set(self.extract_meaningful_words(f"{file_artist} {file_title} {filename}"))
            
            if query_words and file_words:
                word_overlap = len(query_words & file_words) / len(query_words)
                if word_overlap < 0.5:  # Less than 50% word overlap
                    combined_score = min(85, combined_score)  # Reduce suspicious scores
        
        # Apply threshold
        if combined_score < self.threshold:
            combined_score = 0
        
        # Check if this is actually a match
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
        Find matches for a song query with STRICT validation.
        
        Args:
            query_artist (str): Artist to match
            query_title (str): Title to match
            file_metadata_list (list): List of file metadata dictionaries
        
        Returns:
            list: List of match results, sorted by score
        """
        matches = []
        
        logger.debug(f"CONSERVATIVE search: artist='{query_artist}', title='{query_title}' in {len(file_metadata_list)} files")
        
        for metadata in file_metadata_list:
            match_result = self.match_song(query_artist, query_title, metadata)
            
            if match_result['is_match']:
                # Add full metadata to match result
                match_result.update(metadata)
                matches.append(match_result)
        
        # Sort matches by combined score (descending)
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Apply STRICT limits and final filtering
        filtered_matches = []
        for match in matches:
            score = match['combined_score']
            
            # Additional validation for electronic music
            if score >= self.threshold:
                filtered_matches.append(match)
        
        # Limit results to prevent overwhelming results
        limited_matches = filtered_matches[:25]  # Reduced from 50
        
        logger.debug(f"CONSERVATIVE search found {len(matches)} raw matches, {len(limited_matches)} after strict filtering")
        return limited_matches