"""
Automatic search module for batch processing of music file matches.
FIXED VERSION - Consistent with manual search behavior
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
        IMPROVED: Better parsing with multiple separator support.
        
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
        separators = [' - ', ' – ', ': ', ' : ', '_-_', ',', ' | ']
        
        for separator in separators:
            if separator in line:
                parts = line.split(separator, 1)
                if len(parts) == 2:
                    artist = parts[0].strip()
                    title = parts[1].strip()
                    # Don't return empty strings
                    if artist and title:
                        return artist, title
                    elif title:  # Only title available
                        return "", title
        
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
                    original_line = line.strip()
                    
                    # Skip empty lines and comments
                    if not original_line or original_line.startswith('#'):
                        continue
                    
                    artist, title = self._parse_match_line(original_line)
                    if artist is not None or title:
                        pairs.append((line_num, original_line, artist, title))
        
        except Exception as e:
            logger.error(f"Error loading match file {file_path}: {str(e)}")
        
        logger.info(f"Loaded {len(pairs)} artist/title pairs from {file_path}")
        return pairs
    
    def _find_matches_for_pair(self, artist, title, use_pre_filtering=True):
        """
        Find matches for an artist/title pair.
        IMPROVED: Better pre-filtering strategy for artist+title combinations.
        
        Args:
            artist (str): Artist to match
            title (str): Title to match
            use_pre_filtering (bool): Whether to use pre-filtering optimization
        
        Returns:
            list: List of matches sorted by score
        """
        # Use pre-filtering for better performance if enabled and we have search terms
        if use_pre_filtering and (artist or title):
            # Extract key words for pre-filtering
            artist_words = self.string_matcher.extract_key_words(artist) if artist else []
            title_words = self.string_matcher.extract_key_words(title) if title else []
            
            # Special strategy: if we have both artist and title, prioritize title words
            # This helps avoid matches based only on common artist names like "DJ Paul"
            if artist_words and title_words:
                # Use more title words and fewer artist words for pre-filtering
                # This helps find files that actually match the song title
                primary_words = title_words
                secondary_words = artist_words[:2]  # Limit artist words to avoid too many false matches
                all_words = primary_words + secondary_words
                
                logger.debug(f"Artist+Title search: prioritizing title words {title_words} over artist words {artist_words[:2]}")
                
                candidate_files = self.cache_manager.get_candidate_files(
                    artist_words=secondary_words,  # Limited artist words
                    title_words=primary_words,     # Full title words
                    limit=1500  # Slightly smaller limit for more focused results
                )
            elif artist_words:
                candidate_files = self.cache_manager.get_candidate_files(
                    artist_words=artist_words,
                    title_words=None,
                    limit=2000
                )
            elif title_words:
                candidate_files = self.cache_manager.get_candidate_files(
                    artist_words=None,
                    title_words=title_words,
                    limit=2000
                )
            else:
                # Fallback to all files if no key words extracted
                logger.debug(f"No key words found, using all files for '{artist} - {title}'")
                candidate_files = self.cache_manager.get_all_files()
            
            logger.debug(f"Pre-filtering: {len(candidate_files)} candidates for '{artist} - {title}'")
        else:
            # Use all files (same as manual search)
            logger.debug(f"Using all files for '{artist} - {title}'")
            candidate_files = self.cache_manager.get_all_files()
        
        # Use the string matcher to find matches (same logic as manual search)
        matches = self.string_matcher.find_matches(artist, title, candidate_files)
        
        # Additional filtering for artist+title searches - remove weak matches
        if artist and title and len(matches) > 10:
            # If we have many matches and both artist+title, filter out weaker ones
            threshold_boost = 10  # Require 10 points higher for artist+title searches
            filtered_matches = [m for m in matches if m.get('combined_score', 0) >= (self.string_matcher.threshold + threshold_boost)]
            
            if len(filtered_matches) > 0:
                logger.debug(f"Artist+Title filtering: reduced {len(matches)} to {len(filtered_matches)} higher-quality matches")
                matches = filtered_matches
        
        return matches

    def _find_matches_for_pair_parallel(self, artist, title):
        """
        Thread-safe version of _find_matches_for_pair for parallel processing.
        
        Args:
            artist (str): Artist to match
            title (str): Title to match
        
        Returns:
            list: List of matches sorted by score
        """
        try:
            return self._find_matches_for_pair(artist, title, use_pre_filtering=True)
        except Exception as e:
            logger.error(f"Error in parallel worker for '{artist} - {title}': {str(e)}")
            return []
    
    def process_match_file(self, file_path, show_progress=True, use_parallel=True):
        """
        Process a match file and find matches for each entry.
        IMPROVED: Option to disable parallel processing for debugging.
        
        Args:
            file_path (str): Path to match file
            show_progress (bool): Whether to show progress bar
            use_parallel (bool): Whether to use parallel processing
        
        Returns:
            list: List of results for each line containing line, artist, title, matches
        """
        # Load pairs from match file
        pairs = self._load_match_file(file_path)
        
        if not pairs:
            logger.warning(f"No valid entries found in match file: {file_path}")
            return []
        
        # Get cache stats for logging
        cache_stats = self.cache_manager.get_cache_stats()
        logger.info(f"Processing {len(pairs)} entries against {cache_stats['total_files']} indexed files")
        
        if use_parallel and len(pairs) > 5:  # Only use parallel for larger lists
            return self._process_parallel(pairs, show_progress)
        else:
            return self._process_sequential(pairs, show_progress)
    
    def _process_sequential(self, pairs, show_progress=True):
        """
        Process pairs sequentially (useful for debugging).
        
        Args:
            pairs (list): List of (line_num, line, artist, title) tuples
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of results
        """
        results = []
        
        if show_progress:
            progress_bar = tqdm(total=len(pairs), desc="Processing matches (sequential)", unit="entry")
        
        for line_num, line, artist, title in pairs:
            try:
                matches = self._find_matches_for_pair(artist, title, use_pre_filtering=True)
                
                # Create result dictionary
                results.append({
                    'line_num': line_num,
                    'line': line,
                    'artist': artist,
                    'title': title,
                    'matches': matches
                })
                
                logger.debug(f"Sequential: '{artist} - {title}' found {len(matches)} matches")
                
            except Exception as e:
                logger.error(f"Error processing '{artist} - {title}': {str(e)}")
                # Add empty result for failed entries
                results.append({
                    'line_num': line_num,
                    'line': line,
                    'artist': artist,
                    'title': title,
                    'matches': []
                })
            
            if show_progress:
                progress_bar.update(1)
        
        if show_progress:
            progress_bar.close()
        
        logger.info(f"Sequential processing completed for {len(results)} entries")
        return results
    
    def _process_parallel(self, pairs, show_progress=True):
        """
        Process pairs using parallel processing.
        
        Args:
            pairs (list): List of (line_num, line, artist, title) tuples
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of results
        """
        from concurrent.futures import ThreadPoolExecutor
        import multiprocessing
        
        # Determine optimal number of worker threads
        # Use fewer threads than cores to avoid overwhelming the database
        max_workers = min(multiprocessing.cpu_count() // 2, len(pairs), 4)  # Max 4 threads
        max_workers = max(1, max_workers)  # At least 1 thread
        
        logger.info(f"Using {max_workers} parallel workers for processing")
        
        results = []
        
        if show_progress:
            progress_bar = tqdm(total=len(pairs), desc="Processing matches (parallel)", unit="entry")
        
        # Process entries in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_data = {}
            for line_num, line, artist, title in pairs:
                future = executor.submit(self._find_matches_for_pair_parallel, artist, title)
                future_to_data[future] = (line_num, line, artist, title)
            
            # Collect results as they complete
            from concurrent.futures import as_completed
            for future in as_completed(future_to_data):
                line_num, line, artist, title = future_to_data[future]
                
                try:
                    matches = future.result()
                    
                    # Create result dictionary
                    results.append({
                        'line_num': line_num,
                        'line': line,
                        'artist': artist,
                        'title': title,
                        'matches': matches
                    })
                    
                    logger.debug(f"Parallel: '{artist} - {title}' found {len(matches)} matches")
                    
                except Exception as e:
                    logger.error(f"Error processing '{artist} - {title}': {str(e)}")
                    # Add empty result for failed entries
                    results.append({
                        'line_num': line_num,
                        'line': line,
                        'artist': artist,
                        'title': title,
                        'matches': []
                    })
                
                if show_progress:
                    progress_bar.update(1)
        
        if show_progress:
            progress_bar.close()
        
        # Sort results by line number to maintain original order
        results.sort(key=lambda x: x['line_num'])
        
        logger.info(f"Parallel processing completed for {len(results)} entries")
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
    
    def debug_search(self, artist, title, max_candidates=10):
        """
        Debug search function to help diagnose search issues.
        
        Args:
            artist (str): Artist to search for
            title (str): Title to search for
            max_candidates (int): Maximum candidates to show in debug output
        
        Returns:
            dict: Debug information
        """
        logger.info(f"=== DEBUG SEARCH for '{artist} - {title}' ===")
        
        # Extract key words
        artist_words = self.string_matcher.extract_key_words(artist) if artist else []
        title_words = self.string_matcher.extract_key_words(title) if title else []
        
        logger.info(f"Extracted artist words: {artist_words}")
        logger.info(f"Extracted title words: {title_words}")
        
        # Get candidates with pre-filtering
        candidates = self.cache_manager.get_candidate_files(
            artist_words=artist_words,
            title_words=title_words,
            limit=1000
        )
        
        logger.info(f"Pre-filtering found {len(candidates)} candidates")
        
        # Show first few candidates
        for i, candidate in enumerate(candidates[:max_candidates]):
            logger.info(f"Candidate {i+1}: {candidate.get('filename', 'unknown')} "
                       f"(artist: '{candidate.get('artist', '')}', title: '{candidate.get('title', '')}')")
        
        # Find matches
        matches = self.string_matcher.find_matches(artist, title, candidates)
        
        logger.info(f"Fuzzy matching found {len(matches)} matches")
        
        # Show match details
        for i, match in enumerate(matches[:5]):  # Show top 5 matches
            logger.info(f"Match {i+1}: {match.get('filename', 'unknown')} "
                       f"(score: {match.get('combined_score', 0):.1f}%)")
        
        return {
            'query_artist': artist,
            'query_title': title,
            'artist_words': artist_words,
            'title_words': title_words,
            'candidates_count': len(candidates),
            'matches_count': len(matches),
            'top_matches': matches[:5]
        }