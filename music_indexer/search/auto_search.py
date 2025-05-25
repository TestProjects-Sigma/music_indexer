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
        Find matches for an artist/title pair using pre-filtering for better performance.
        
        Args:
            artist (str): Artist to match
            title (str): Title to match
            all_files (list): List of file metadata dictionaries (not used with pre-filtering)
        
        Returns:
            list: List of matches sorted by score
        """
        # Extract key words for pre-filtering
        artist_words = self.string_matcher.extract_key_words(artist) if artist else []
        title_words = self.string_matcher.extract_key_words(title) if title else []
        
        # If we have key words, use pre-filtering
        if artist_words or title_words:
            candidate_files = self.cache_manager.get_candidate_files(
                artist_words=artist_words,
                title_words=title_words,
                limit=1000  # Limit candidates for performance
            )
            
            logger.debug(f"Pre-filtering: {len(candidate_files)} candidates for '{artist} - {title}'")
            
            # Use the candidates for fuzzy matching
            matches = self.string_matcher.find_matches(artist, title, candidate_files)
        else:
            # Fallback to original method if no key words
            logger.debug(f"No key words found, using full search for '{artist} - {title}'")
            matches = self.string_matcher.find_matches(artist, title, all_files)
        
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
            # Extract key words for pre-filtering
            artist_words = self.string_matcher.extract_key_words(artist) if artist else []
            title_words = self.string_matcher.extract_key_words(title) if title else []
            
            # If we have key words, use pre-filtering
            if artist_words or title_words:
                candidate_files = self.cache_manager.get_candidate_files(
                    artist_words=artist_words,
                    title_words=title_words,
                    limit=500  # Reduced limit for parallel processing
                )
                
                logger.debug(f"Pre-filtering: {len(candidate_files)} candidates for '{artist} - {title}'")
                
                # Use the candidates for fuzzy matching
                matches = self.string_matcher.find_matches(artist, title, candidate_files)
            else:
                # Fallback: get a reasonable subset of files for matching
                logger.debug(f"No key words found, using limited search for '{artist} - {title}'")
                all_files = self.cache_manager.get_all_files(limit=5000)  # Limit for performance
                matches = self.string_matcher.find_matches(artist, title, all_files)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error in parallel worker for '{artist} - {title}': {str(e)}")
            return []
    
    def process_match_file(self, file_path, show_progress=True):
        """
        Process a match file and find matches for each entry using parallel processing.
        
        Args:
            file_path (str): Path to match file
            show_progress (bool): Whether to show progress bar
        
        Returns:
            list: List of results for each line containing line, artist, title, matches
        """
        from concurrent.futures import ThreadPoolExecutor
        import multiprocessing
        
        # Load pairs from match file
        pairs = self._load_match_file(file_path)
        
        if not pairs:
            logger.warning(f"No valid entries found in match file: {file_path}")
            return []
        
        # Get cache stats for logging
        cache_stats = self.cache_manager.get_cache_stats()
        logger.info(f"Processing {len(pairs)} entries against {cache_stats['total_files']} indexed files")
        
        # Determine optimal number of worker threads
        # Use number of CPU cores, but cap it to avoid overwhelming the system
        max_workers = min(multiprocessing.cpu_count(), len(pairs), 8)  # Max 8 threads
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
