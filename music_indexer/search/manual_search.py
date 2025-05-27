"""
Manual search module for searching music files.
FIXED VERSION - Improved consistency and search logic
"""
from ..core.cache_manager import CacheManager
from ..search.string_matcher import StringMatcher
from ..utils.logger import get_logger

logger = get_logger()


class ManualSearch:
    """
    Provides manual search functionality for music files.
    """
    
    def __init__(self, cache_manager=None, string_matcher=None):
        """
        Initialize manual search with specified components.
        
        Args:
            cache_manager (CacheManager): Cache manager instance
            string_matcher (StringMatcher): String matcher instance
        """
        self.cache_manager = cache_manager or CacheManager()
        self.string_matcher = string_matcher or StringMatcher()
        logger.info("Manual search initialized")
    
    def search(self, query=None, artist=None, title=None, album=None, format_type=None, exact_match=False):
        """
        Search for music files based on specified criteria.
        IMPROVED: Better fuzzy search logic and consistency.
        
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
        if exact_match:
            # Use database search for exact matching
            results = self.cache_manager.search_files(
                query=query,
                artist=artist,
                title=title,
                album=album,
                format_type=format_type
            )
            
            # Add match score of 100 to indicate exact match
            for result in results:
                result['combined_score'] = 100
                result['is_match'] = True
            
            logger.info(f"Exact search found {len(results)} results")
            return results
        
        else:
            # Fuzzy search
            logger.info(f"Starting fuzzy search: query='{query}', artist='{artist}', title='{title}', album='{album}', format='{format_type}'")
            
            # Get all files from cache first
            all_files = self.cache_manager.get_all_files()
            logger.info(f"Retrieved {len(all_files)} files from cache for fuzzy search")
            
            # Pre-filter results based on format if specified
            if format_type:
                all_files = [f for f in all_files if f.get('format', '').lower() == format_type.lower()]
                logger.info(f"After format filtering: {len(all_files)} files")
            
            filtered_files = all_files
            
            # If general query provided, use fuzzy matching across multiple fields
            if query and not (artist or title or album):
                logger.info(f"Performing general query search for: '{query}'")
                matches = []
                
                for file in filtered_files:
                    # Calculate match scores for different fields
                    artist_score = self.string_matcher.match_strings(query, file.get('artist', ''))
                    title_score = self.string_matcher.match_strings(query, file.get('title', ''))
                    album_score = self.string_matcher.match_strings(query, file.get('album', ''))
                    filename_score = self.string_matcher.match_against_filename(query, file.get('filename', ''))
                    
                    # Use highest score
                    max_score = max(artist_score, title_score, album_score, filename_score)
                    
                    if max_score >= self.string_matcher.threshold:
                        file_copy = file.copy()
                        file_copy['combined_score'] = max_score
                        file_copy['is_match'] = True
                        # Add individual scores for debugging
                        file_copy['artist_score'] = artist_score
                        file_copy['title_score'] = title_score
                        file_copy['album_score'] = album_score
                        file_copy['filename_score'] = filename_score
                        matches.append(file_copy)
                
                # Sort by score
                matches.sort(key=lambda x: x['combined_score'], reverse=True)
                logger.info(f"General query fuzzy search found {len(matches)} results")
                return matches
            
            # If specific fields provided, use string matcher to find matches
            else:
                logger.info(f"Performing field-specific search: artist='{artist}', title='{title}', album='{album}'")
                
                # For field-specific searches, use the same logic as auto search for consistency
                if album:
                    # If album is specified, we need to handle it specially since find_matches doesn't support album
                    matches = []
                    
                    for file in filtered_files:
                        # First check if album matches if specified
                        album_score = 0
                        if album:
                            album_score = self.string_matcher.match_strings(album, file.get('album', ''))
                            if album_score < self.string_matcher.threshold:
                                continue  # Skip files where album doesn't match
                        
                        # Then use normal matching for artist/title
                        match_result = self.string_matcher.match_song(artist or "", title or "", file)
                        
                        if match_result['is_match']:
                            # Combine album score if applicable
                            if album:
                                # Adjust combined score to include album matching
                                original_score = match_result['combined_score']
                                match_result['combined_score'] = (original_score + album_score) / 2
                                match_result['album_score'] = album_score
                            
                            # Add full metadata to match result
                            match_result.update(file)
                            matches.append(match_result)
                    
                    # Sort by combined score
                    matches.sort(key=lambda x: x['combined_score'], reverse=True)
                    logger.info(f"Field-specific search with album found {len(matches)} results")
                    return matches
                
                else:
                    # Use standard find_matches method (same as auto search)
                    matches = self.string_matcher.find_matches(artist or "", title or "", filtered_files)
                    logger.info(f"Field-specific search found {len(matches)} results")
                    return matches
    
    def set_similarity_threshold(self, threshold):
        """
        Set the similarity threshold for fuzzy matching.
        
        Args:
            threshold (int): New similarity threshold (0-100)
        """
        self.string_matcher.set_threshold(threshold)
    
    def debug_search(self, query=None, artist=None, title=None, album=None, format_type=None):
        """
        Debug search function to help diagnose search issues.
        
        Args:
            query (str): General search query
            artist (str): Artist name to match
            title (str): Title to match
            album (str): Album to match
            format_type (str): File format to match
        
        Returns:
            dict: Debug information
        """
        logger.info("=== DEBUG MANUAL SEARCH ===")
        logger.info(f"Query: '{query}', Artist: '{artist}', Title: '{title}', Album: '{album}', Format: '{format_type}'")
        
        # Get all