"""
Manual search module for searching music files.
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
            # Get all files from cache first
            all_files = self.cache_manager.get_all_files()
            logger.info(f"Retrieved {len(all_files)} files from cache for fuzzy search")
            
            # Pre-filter results based on format if specified
            if format_type:
                all_files = [f for f in all_files if f.get('format') == format_type]
            
            # If basic query provided, use string matcher to filter
            filtered_files = all_files
            
            # If general query, try to match against multiple fields
            if query and not (artist or title or album):
                matches = []
                
                for file in filtered_files:
                    # Calculate match scores for different fields
                    artist_score = self.string_matcher.match_strings(query, file.get('artist', ''))
                    title_score = self.string_matcher.match_strings(query, file.get('title', ''))
                    album_score = self.string_matcher.match_strings(query, file.get('album', ''))
                    filename_score = self.string_matcher.match_strings(query, file.get('filename', ''))
                    
                    # Use highest score
                    max_score = max(artist_score, title_score, album_score, filename_score)
                    
                    if max_score >= self.string_matcher.threshold:
                        file_copy = file.copy()
                        file_copy['combined_score'] = max_score
                        file_copy['is_match'] = True
                        matches.append(file_copy)
                
                # Sort by score
                matches.sort(key=lambda x: x['combined_score'], reverse=True)
                logger.info(f"Fuzzy search with query '{query}' found {len(matches)} results")
                return matches
            
            # If specific fields provided, use string matcher to find matches
            else:
                matches = self.string_matcher.find_matches(artist, title, filtered_files)
                logger.info(f"Fuzzy search with artist='{artist}', title='{title}' found {len(matches)} results")
                return matches
    
    def set_similarity_threshold(self, threshold):
        """
        Set the similarity threshold for fuzzy matching.
        
        Args:
            threshold (int): New similarity threshold (0-100)
        """
        self.string_matcher.set_threshold(threshold)
