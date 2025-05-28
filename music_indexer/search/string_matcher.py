"""
String matcher module for flexible matching of music files.
COMPLETELY REWRITTEN VERSION - Conservative and accurate matching
"""
from fuzzywuzzy import fuzz
import re

from ..utils.logger import get_logger
logger = get_logger()


class StringMatcher:
    """
    Provides string matching functionality for music files.
    REWRITTEN: Much more conservative and accurate approach.
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
        CONSERVATIVE: Only basic cleaning to preserve meaning.
        
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
        
        # Replace common separators with spaces, but be conservative
        text = re.sub(r'[_\-.]', ' ', text)
        
        # Remove parentheses content that might be remix info, but keep the base
        # Only remove if it's clearly remix/mix info
        remix_patterns = [
            r'\s*\([^)]*remix[^)]*\)\s*$',
            r'\s*\([^)]*mix[^)]*\)\s*$',
            r'\s*\([^)]*edit[^)]*\)\s*$',
            r'\s*\([^)]*remaster[^)]*\)\s*$',
        ]
        
        for pattern in remix_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove leading numbers and dashes (track numbers)
        text = re.sub(r'^\d+[\s\-_]*', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def extract_meaningful_words(self, text):
        """
        Extract meaningful words from text, filtering out noise.
        
        Args:
            text (str): Text to extract words from
        
        Returns:
            list: List of meaningful words
        """
        if not text:
            return []
        
        cleaned = self.clean_string(text)
        words = cleaned.split()
        
        # Filter out very short words and common stop words
        stop_words = {
            'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'is', 'are', 
            'was', 'were', 'vs', 'feat', 'ft', 'dj', 'mc', 'remix', 'mix', 'edit',
            'original', 'radio', 'extended', 'club', 'radio', 'remaster', 'remastered'
        }
        
        meaningful_words = []
        for word in words:
            if len(word) >= 3 and word.lower() not in stop_words:
                meaningful_words.append(word)
        
        return meaningful_words

    def exact_word_match_score(self, search_words, target_words):
        """
        Calculate score based on exact word matches.
        This is the primary scoring method.
        
        Args:
            search_words (list): Words from search term
            target_words (list): Words from target text
        
        Returns:
            int: Match score (0-100)
        """
        if not search_words or not target_words:
            return 0
        
        search_set = {word.lower() for word in search_words}
        target_set = {word.lower() for word in target_words}
        
        # Count exact matches
        matches = search_set & target_set
        
        if not matches:
            return 0
        
        # Calculate score based on coverage
        search_coverage = len(matches) / len(search_set)
        target_coverage = len(matches) / len(target_set)
        
        # Use the average coverage, but require good coverage on search side
        if search_coverage < 0.5:  # At least 50% of search words must match
            return 0
        
        score = (search_coverage + target_coverage) / 2 * 100
        return min(95, int(score))  # Cap at 95 to leave room for fuzzy improvements

    def fuzzy_word_match_score(self, search_words, target_words):
        """
        Calculate fuzzy score between word lists.
        Used as secondary scoring when exact matches fail.
        
        Args:
            search_words (list): Words from search term
            target_words (list): Words from target text
        
        Returns:
            int: Match score (0-100)
        """
        if not search_words or not target_words:
            return 0
        
        total_score = 0
        matched_words = 0
        
        for search_word in search_words:
            if len(search_word) < 3:  # Skip very short words
                continue
                
            best_word_score = 0
            for target_word in target_words:
                if len(target_word) < 3:
                    continue
                
                # Only use ratio - avoid token_set_ratio which causes false matches
                word_score = fuzz.ratio(search_word.lower(), target_word.lower())
                best_word_score = max(best_word_score, word_score)
            
            # Only count words with strong similarity
            if best_word_score >= 85:  # Strict threshold for fuzzy matching
                total_score += best_word_score
                matched_words += 1
        
        if matched_words == 0:
            return 0
        
        # Require at least 50% of search words to have strong fuzzy matches
        if matched_words / len(search_words) < 0.5:
            return 0
        
        average_score = total_score / matched_words
        # Reduce fuzzy scores to prefer exact matches
        return max(0, int(average_score * 0.8))  # 20% penalty for fuzzy vs exact

    def match_strings(self, str1, str2):
        """
        Match two strings using conservative approach.
        
        Args:
            str1 (str): First string (search term)
            str2 (str): Second string (target)
        
        Returns:
            int: Similarity score (0-100)
        """
        if not str1 or not str2:
            return 0
        
        # Extract meaningful words
        search_words = self.extract_meaningful_words(str1)
        target_words = self.extract_meaningful_words(str2)
        
        if not search_words or not target_words:
            return 0
        
        # Try exact word matching first
        exact_score = self.exact_word_match_score(search_words, target_words)
        
        if exact_score > 0:
            return exact_score
        
        # Fall back to fuzzy matching only if exact fails
        fuzzy_score = self.fuzzy_word_match_score(search_words, target_words)
        
        return fuzzy_score

    def match_against_filename(self, query, filename):
        """
        Match query against filename with special filename handling.
        
        Args:
            query (str): Search query
            filename (str): Filename to match against
        
        Returns:
            int: Match score (0-100)
        """
        if not query or not filename:
            return 0
        
        # For filenames, we need to be even more careful
        # because they often contain multiple pieces of info
        
        # First try normal string matching
        normal_score = self.match_strings(query, filename)
        
        if normal_score >= 80:  # High confidence
            return normal_score
        
        # Try matching against parts of the filename
        # Common filename format: "artist - title" or "number - artist - title"
        filename_parts = re.split(r'\s*-\s*', self.clean_string(filename))
        
        best_part_score = 0
        for part in filename_parts:
            if len(part.strip()) >= 3:  # Skip very short parts
                part_score = self.match_strings(query, part)
                best_part_score = max(best_part_score, part_score)
        
        # Return the better of the two approaches
        return max(normal_score, best_part_score)

    def match_song(self, query_artist, query_title, file_metadata):
        """
        Match a song query against file metadata using conservative approach.
        
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
        
        # Match artist if provided
        if query_artist and len(query_artist.strip()) >= 2:
            if file_artist:
                artist_score = self.match_strings(query_artist, file_artist)
            
            # Also try against filename if metadata match is weak
            if artist_score < 70 and filename:
                filename_artist_score = self.match_against_filename(query_artist, filename)
                artist_score = max(artist_score, filename_artist_score)
        
        # Match title if provided
        if query_title and len(query_title.strip()) >= 2:
            if file_title:
                title_score = self.match_strings(query_title, file_title)
            
            # Also try against filename if metadata match is weak
            if title_score < 70 and filename:
                filename_title_score = self.match_against_filename(query_title, filename)
                title_score = max(title_score, filename_title_score)
        
        # Calculate combined score with strict requirements
        combined_score = 0
        
        if query_artist and query_title:
            # Both artist and title provided - require both to match reasonably well
            min_threshold = max(60, self.threshold - 15)
            
            if artist_score >= min_threshold and title_score >= min_threshold:
                # Both match - use weighted average
                combined_score = (artist_score * 0.6 + title_score * 0.4)
            elif max(artist_score, title_score) >= 85:
                # One very strong match can compensate
                combined_score = max(artist_score, title_score) * 0.8
            else:
                # Try filename matching as last resort
                if filename:
                    full_query = f"{query_artist} {query_title}".strip()
                    filename_score = self.match_against_filename(full_query, filename)
                    if filename_score >= 75:
                        combined_score = filename_score * 0.7
        
        elif query_artist:
            # Only artist provided
            combined_score = artist_score
        elif query_title:
            # Only title provided
            combined_score = title_score
        
        # Final validation - ensure score makes sense
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
        Find matches for a song query in a list of file metadata.
        
        Args:
            query_artist (str): Artist to match
            query_title (str): Title to match
            file_metadata_list (list): List of file metadata dictionaries
        
        Returns:
            list: List of match results, sorted by score
        """
        matches = []
        
        logger.debug(f"Conservative search: artist='{query_artist}', title='{query_title}' in {len(file_metadata_list)} files")
        
        for metadata in file_metadata_list:
            match_result = self.match_song(query_artist, query_title, metadata)
            
            if match_result['is_match']:
                # Add full metadata to match result
                match_result.update(metadata)
                matches.append(match_result)
        
        # Sort matches by combined score (descending)
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Apply stricter limits and filtering
        # Remove matches with suspiciously perfect scores that might be false positives
        filtered_matches = []
        for match in matches:
            score = match['combined_score']
            
            # Flag suspicious 100% scores on weak matches
            if score >= 99:
                # Verify this is actually a strong match
                artist_words = self.extract_meaningful_words(query_artist or "")
                title_words = self.extract_meaningful_words(query_title or "")
                file_artist_words = self.extract_meaningful_words(match.get('artist', ''))
                file_title_words = self.extract_meaningful_words(match.get('title', ''))
                
                # Check if we have substantial word overlap
                search_words = set(artist_words + title_words)
                file_words = set(file_artist_words + file_title_words)
                
                if len(search_words) > 0:
                    overlap = len(search_words & file_words) / len(search_words)
                    if overlap < 0.4:  # Less than 40% word overlap
                        # Reduce score for suspicious matches
                        match['combined_score'] = min(85, score)
                        logger.debug(f"Reduced suspicious 100% score for {match.get('filename', 'unknown')}")
            
            if match['combined_score'] >= self.threshold:
                filtered_matches.append(match)
        
        # Limit results
        limited_matches = filtered_matches[:30]  # Reduced from 50
        
        logger.debug(f"Conservative search found {len(matches)} raw matches, {len(limited_matches)} after filtering")
        return limited_matches