"""
Auto search that primarily uses the proven "general query" logic from manual search.
OPTIMIZED VERSION - Uses the same successful general query approach
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
    Auto search that uses the proven general query approach.
    OPTIMIZED: Primary strategy is general query (like successful manual search).
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
        logger.info("General query auto search initialized")
    
    def _parse_match_line(self, line):
        """
        Parse a line from a match file - keep it simple.
        
        Args:
            line (str): Line to parse
        
        Returns:
            dict: Parsed information
        """
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            return None
        
        # For auto search, we'll primarily use the original line as general query
        # But also extract artist/title for potential fallback
        original_line = line
        
        # Try to parse artist and title with common separators
        separators = [' - ', ' – ', ': ', ' : ', '_-_', ',', ' | ']
        
        artist = ""
        title = ""
        
        for separator in separators:
            if separator in line:
                parts = line.split(separator, 1)
                if len(parts) == 2:
                    artist = parts[0].strip()
                    title = parts[1].strip()
                    break
        
        # If no separator found, treat whole line as title
        if not artist and not title:
            title = line
        
        return {
            'original_line': original_line,
            'artist': artist,
            'title': title
        }
    
    def _load_match_file(self, file_path):
        """Load and parse match file."""
        if not os.path.exists(file_path):
            logger.error(f"Match file not found: {file_path}")
            return []
        
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    parsed = self._parse_match_line(line)
                    if parsed:
                        entries.append((line_num, parsed))
        
        except Exception as e:
            logger.error(f"Error loading match file {file_path}: {str(e)}")
        
        logger.info(f"Loaded {len(entries)} entries from {file_path}")
        return entries
    
    def _find_matches_general_query_exact(self, query):
        """
        Find matches using EXACT same logic as manual search "general query".
        OPTIMIZED: Uses smart pre-filtering for better performance.
        
        Args:
            query (str): Search query
        
        Returns:
            list: List of matches (exactly like manual search)
        """
        if not query or len(query.strip()) < 3:
            return []
        
        logger.debug(f"General query search for: '{query}'")
        
        # PERFORMANCE OPTIMIZATION: Use smart pre-filtering for large collections
        cache_stats = self.cache_manager.get_cache_stats()
        total_files = cache_stats.get('total_files', 0)
        
        if total_files > 10000:
            # Extract key words for pre-filtering
            query_words = self._extract_query_words(query)
            
            if query_words and len(query_words) >= 2:
                # Use pre-filtering with generous limits
                candidate_files = self.cache_manager.get_candidate_files(
                    artist_words=query_words[:3],  # First 3 words as artist keywords
                    title_words=query_words[:3],   # First 3 words as title keywords  
                    limit=5000  # Generous limit to avoid missing matches
                )
                
                logger.debug(f"Pre-filtering: {len(candidate_files)} candidates from {total_files} files")
                
                # Safety check: if pre-filtering returns too few results, fall back to all files
                if len(candidate_files) < 50:
                    logger.debug("Too few candidates, using all files")
                    candidate_files = self.cache_manager.get_all_files()
            else:
                # No good keywords, use all files
                candidate_files = self.cache_manager.get_all_files()
        else:
            # Small collection, use all files
            candidate_files = self.cache_manager.get_all_files()
        
        matches = []
        
        for file_metadata in candidate_files:
            # Test against multiple fields (EXACT same as manual search)
            artist = file_metadata.get('artist', '')
            title = file_metadata.get('title', '')
            album = file_metadata.get('album', '')
            filename = file_metadata.get('filename', '')
            
            # Calculate match scores for different fields (EXACT same logic)
            artist_score = self.string_matcher.match_strings(query, artist) if artist else 0
            title_score = self.string_matcher.match_strings(query, title) if title else 0
            album_score = self.string_matcher.match_strings(query, album) if album else 0
            filename_score = self.string_matcher.match_against_filename(query, filename) if filename else 0
            
            # Use highest score (EXACT same as manual search)
            max_score = max(artist_score, title_score, album_score, filename_score)
            
            if max_score >= self.string_matcher.threshold:
                # Create match result (same format as manual search)
                match_result = {
                    'file_path': file_metadata.get('file_path', ''),
                    'artist': artist,
                    'title': title,
                    'filename': filename,
                    'artist_score': artist_score,
                    'title_score': title_score,
                    'album_score': album_score,
                    'filename_score': filename_score,
                    'combined_score': max_score,
                    'is_match': True
                }
                
                # Add full metadata
                match_result.update(file_metadata)
                matches.append(match_result)
        
        # Sort by combined score (descending) - same as manual search
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Limit results (same as manual search)
        limited_matches = matches[:50]  # Use same limit as manual search
        
        logger.debug(f"General query found {len(matches)} matches (showing top {len(limited_matches)})")
        
        return limited_matches
    
    def _extract_query_words(self, query):
        """
        Extract meaningful words from query for pre-filtering.
        
        Args:
            query (str): Search query
        
        Returns:
            list: List of meaningful words
        """
        if not query:
            return []
        
        # Clean and extract words
        cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
        words = cleaned.split()
        
        # Filter meaningful words
        stop_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'is', 'are', 'was', 'were'}
        meaningful_words = [w for w in words if len(w) >= 3 and w not in stop_words]
        
        return meaningful_words
    
    def _find_matches_for_entry(self, parsed_info):
        """
        Find matches for a single entry using proven strategies.
        
        Args:
            parsed_info (dict): Parsed search information
        
        Returns:
            list: List of matches
        """
        original_line = parsed_info['original_line']
        artist = parsed_info['artist']
        title = parsed_info['title']
        
        logger.debug(f"Processing: '{original_line}'")
        
        # STRATEGY 1: General query (PRIMARY - this is what works!)
        # Use the exact same logic as successful manual search
        matches = self._find_matches_general_query_exact(original_line)
        
        # If we got good matches, return them
        if matches and matches[0].get('combined_score', 0) >= 90:
            logger.debug(f"General query found excellent match ({matches[0]['combined_score']:.1f}%) for '{original_line}'")
            return matches
        
        # STRATEGY 2: Try title-only if we have a clear title and general query was weak
        if title and len(title) >= 4 and (not matches or matches[0].get('combined_score', 0) < 80):
            logger.debug(f"Trying title-only search for: '{title}'")
            title_matches = self._find_matches_general_query_exact(title)
            
            # If title search found better matches, use those
            if title_matches and (not matches or 
                title_matches[0].get('combined_score', 0) > matches[0].get('combined_score', 0)):
                matches = title_matches
        
        # STRATEGY 3: Try clean version without remix info as last resort
        if not matches or matches[0].get('combined_score', 0) < 75:
            clean_line = self._remove_remix_info(original_line)
            if clean_line != original_line and len(clean_line) >= 4:
                logger.debug(f"Trying clean version: '{clean_line}'")
                clean_matches = self._find_matches_general_query_exact(clean_line)
                
                # If clean version found better matches, use those
                if clean_matches and (not matches or 
                    clean_matches[0].get('combined_score', 0) > matches[0].get('combined_score', 0)):
                    matches = clean_matches
        
        return matches or []
    
    def _remove_remix_info(self, text):
        """Remove remix/version information from text."""
        if not text:
            return text
        
        # Common remix patterns to remove
        remix_patterns = [
            r'\s*-\s*[^-]*remix[^-]*$',
            r'\s*-\s*[^-]*mix[^-]*$', 
            r'\s*-\s*[^-]*edit[^-]*$',
            r'\s*-\s*original[^-]*$',
            r'\s*-\s*radio[^-]*$',
            r'\s*\([^)]*remix[^)]*\)\s*$',
            r'\s*\([^)]*mix[^)]*\)\s*$',
        ]
        
        cleaned = text
        for pattern in remix_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def process_match_file(self, file_path, show_progress=True, use_parallel=False):
        """
        Process a match file using general query approach.
        
        Args:
            file_path (str): Path to match file
            show_progress (bool): Whether to show progress bar
            use_parallel (bool): Whether to use parallel processing (ignored)
        
        Returns:
            list: List of results for each line
        """
        # Load entries from match file
        entries = self._load_match_file(file_path)
        
        if not entries:
            logger.warning(f"No valid entries found in match file: {file_path}")
            return []
        
        # Get cache stats for logging
        cache_stats = self.cache_manager.get_cache_stats()
        logger.info(f"General query processing {len(entries)} entries against {cache_stats['total_files']} indexed files")
        
        # Process sequentially (reliable and fast enough)
        return self._process_sequential(entries, show_progress)
    
    def _process_sequential(self, entries, show_progress=True):
        """
        Process entries sequentially using general query approach.
        
        Args:
            entries (list): List of (line_num, parsed_info) tuples
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of results
        """
        results = []
        
        if show_progress:
            progress_bar = tqdm(total=len(entries), desc="General query auto search", unit="entry")
        
        for line_num, parsed_info in entries:
            try:
                # Use general query approach
                matches = self._find_matches_for_entry(parsed_info)
                
                # Create result dictionary
                results.append({
                    'line_num': line_num,
                    'line': parsed_info['original_line'],
                    'artist': parsed_info['artist'],
                    'title': parsed_info['title'],
                    'matches': matches
                })
                
                if matches:
                    best_score = matches[0].get('combined_score', 0)
                    logger.debug(f"'{parsed_info['original_line']}' -> {len(matches)} matches (best: {best_score:.1f}%)")
                else:
                    logger.debug(f"'{parsed_info['original_line']}' -> No matches")
                
            except Exception as e:
                logger.error(f"Error processing '{parsed_info['original_line']}': {str(e)}")
                # Add empty result for failed entries
                results.append({
                    'line_num': line_num,
                    'line': parsed_info['original_line'],
                    'artist': parsed_info['artist'],
                    'title': parsed_info['title'],
                    'matches': []
                })
            
            if show_progress:
                progress_bar.update(1)
        
        if show_progress:
            progress_bar.close()
        
        logger.info(f"General query processing completed for {len(results)} entries")
        return results
    
    def save_results(self, results, output_file):
        """Save search results to a file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write("# General Query Auto Search Results\n")
                file.write("# Uses same logic as successful manual 'general query' search\n")
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
        """Set the similarity threshold for fuzzy matching."""
        self.string_matcher.set_threshold(threshold)
    
    def debug_search(self, query, max_candidates=10):
        """
        Debug search function to help diagnose search issues.
        
        Args:
            query (str): Query to search for
            max_candidates (int): Maximum candidates to show in debug output
        
        Returns:
            dict: Debug information
        """
        logger.info(f"=== DEBUG GENERAL QUERY SEARCH for '{query}' ===")
        
        # Find matches using general query
        matches = self._find_matches_general_query_exact(query)
        
        logger.info(f"General query found {len(matches)} matches")
        
        # Show match details
        for i, match in enumerate(matches[:max_candidates]):
            logger.info(f"Match {i+1}: {match.get('filename', 'unknown')} "
                       f"(score: {match.get('combined_score', 0):.1f}%)")
        
        return {
            'query': query,
            'matches_count': len(matches),
            'top_matches': matches[:max_candidates]
        }