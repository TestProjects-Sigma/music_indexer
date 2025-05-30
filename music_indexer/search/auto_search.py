"""
Fixed auto search that properly handles track numbers and underscores in electronic music files.
CRITICAL FIX: Handles filenames like "01-omi_-_the_claim-nrg.mp3" correctly.
"""
import os
import re
from tqdm import tqdm
from fuzzywuzzy import fuzz

from ..core.cache_manager import CacheManager
from ..search.string_matcher import StringMatcher
from ..utils.logger import get_logger
from ..utils.enhanced_playlist_parser import enhance_auto_search_with_parser

logger = get_logger()


class EnhancedStringMatcher(StringMatcher):
    """
    Enhanced string matcher that properly handles electronic music file naming patterns.
    """
    
    def clean_string(self, text):
        """
        Enhanced clean_string method for electronic music files.
        CRITICAL: Fixes track number parsing issues.
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove file extensions
        text = re.sub(r'\.(mp3|flac|m4a|aac|wav|ogg)$', '', text, flags=re.IGNORECASE)
        
        # CRITICAL FIX: Remove track numbers at the beginning
        # This fixes the "01" artist problem you found
        track_patterns = [
            r'^\d{1,3}[-_\.\s]+',       # 01-, 001_, 1., 01 
            r'^[a-z]\d{1,2}[-_\.\s]+',  # a01-, b1_, etc.
            r'^[a-z]{2,5}\d*[-_\.\s]+', # nrg01-, promo_, etc.
        ]
        
        for pattern in track_patterns:
            text = re.sub(pattern, '', text)
        
        # CRITICAL FIX: Handle underscore patterns properly
        # This is key for your files with underscores
        text = re.sub(r'_-_', ' - ', text)  # artist_-_title -> artist - title
        text = re.sub(r'_+', ' ', text)     # multiple underscores -> space
        
        # Replace other separators with spaces, but be careful with dashes
        text = re.sub(r'[.]', ' ', text)
        text = re.sub(r'[-]', ' ', text)  # Convert dashes to spaces for better word matching
        
        # Remove remix/version info that adds noise
        remix_patterns = [
            r'\s+(original\s+)?mix\s*$',
            r'\s+(radio\s+)?(edit|version)\s*$',
            r'\s+remaster(ed)?\s*$',
            r'\s+\d{4}\s*$',  # Remove years
        ]
        
        for pattern in remix_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def match_against_filename(self, query, filename):
        """
        Enhanced filename matching for electronic music files.
        CRITICAL: Better handling of your file naming patterns.
        """
        if not query or not filename:
            return 0
        
        # Clean both query and filename with our enhanced cleaning
        clean_query = self.clean_string(query)
        clean_filename = self.clean_string(filename)
        
        logger.debug(f"Filename matching: '{query}' -> '{clean_query}' vs '{filename}' -> '{clean_filename}'")
        
        scores = []
        
        # 1. Direct match after cleaning
        direct_score = self.match_strings(clean_query, clean_filename)
        scores.append(direct_score)
        logger.debug(f"  Direct score: {direct_score}")
        
        # 2. Try to parse artist-title from filename and match components
        artist, title = self.extract_artist_title_from_cleaned_filename(clean_filename)
        
        if artist and title:
            logger.debug(f"  Parsed filename: artist='{artist}', title='{title}'")
            
            # Match query against extracted artist
            artist_score = self.match_strings(clean_query, artist)
            scores.append(artist_score)
            
            # Match query against extracted title  
            title_score = self.match_strings(clean_query, title)
            scores.append(title_score)
            
            # Match query against combined "artist title"
            combined = f"{artist} {title}"
            combined_score = self.match_strings(clean_query, combined)
            scores.append(combined_score)
            
            logger.debug(f"  Component scores: artist={artist_score}, title={title_score}, combined={combined_score}")
        
        # 3. Word-by-word matching for complex queries
        query_words = self.extract_meaningful_words(clean_query)
        filename_words = self.extract_meaningful_words(clean_filename)
        
        if query_words and filename_words:
            word_matches = 0
            total_words = len(query_words)
            
            for query_word in query_words:
                best_word_match = 0
                for filename_word in filename_words:
                    if len(query_word) >= 3 and len(filename_word) >= 3:
                        word_similarity = fuzz.ratio(query_word, filename_word)
                        best_word_match = max(best_word_match, word_similarity)
                
                if best_word_match >= 80:  # Good word match
                    word_matches += 1
            
            if word_matches > 0:
                word_score = (word_matches / total_words) * 90
                scores.append(word_score)
                logger.debug(f"  Word matching: {word_matches}/{total_words} words matched, score={word_score}")
        
        # Return the best score
        best_score = max(scores) if scores else 0
        
        if best_score > 0:
            logger.debug(f"  Final filename score: {best_score:.1f}")
        
        return best_score

    def extract_artist_title_from_cleaned_filename(self, cleaned_filename):
        """
        Extract artist and title from a cleaned filename.
        Specifically handles electronic music naming patterns.
        """
        if not cleaned_filename:
            return None, None
        
        # Try different separator patterns
        # After cleaning, we should have "artist title" or similar
        words = cleaned_filename.split()
        
        if len(words) < 2:
            return None, None
        
        # For electronic music, often the pattern is:
        # "artist name track title" or "artist track title"
        
        # Try splitting roughly in half
        if len(words) >= 4:
            mid = len(words) // 2
            artist = ' '.join(words[:mid])
            title = ' '.join(words[mid:])
            
            if len(artist) >= 2 and len(title) >= 2:
                return artist, title
        
        # For shorter names, try first word(s) as artist, rest as title
        if len(words) >= 3:
            artist = words[0]
            title = ' '.join(words[1:])
            
            if len(artist) >= 2 and len(title) >= 2:
                return artist, title
        
        return None, None

    def extract_meaningful_words(self, text):
        """
        Enhanced word extraction for electronic music.
        """
        if not text:
            return []
        
        # Split into words
        words = text.split()
        
        # Enhanced stop words for electronic music
        stop_words = {
            'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'is', 'are', 
            'was', 'were', 'vs', 'feat', 'ft', 'dj', 'mc', 'remix', 'mix', 'edit',
            'original', 'radio', 'extended', 'club', 'vocal', 'instrumental',
            'remaster', 'remastered', 'rework', 'bootleg', 'mashup', 'vol', 'pt',
            'part', 'ep', 'lp', 'single', 'promo', 'white', 'label', 'vinyl',
            'digital', 'wav', 'mp3', 'flac', 'kbps', 'hz', 'nrg'
        }
        
        meaningful_words = []
        for word in words:
            # Filter criteria - be more strict to avoid noise
            if (len(word) >= 3 and 
                word.lower() not in stop_words and 
                not word.isdigit() and
                not re.match(r'^\d+$', word) and
                not re.match(r'^[a-z]\d+$', word.lower())):  # Skip things like "a1", "b2"
                meaningful_words.append(word)
        
        return meaningful_words


class AutoSearch:
    """
    Fixed auto search that properly handles electronic music file naming patterns.
    """
    
    def __init__(self, cache_manager=None, string_matcher=None):
        """
        Initialize automatic search with enhanced string matcher.
        """
        self.cache_manager = cache_manager or CacheManager()
        # Use the enhanced string matcher with lower threshold
        self.string_matcher = string_matcher or EnhancedStringMatcher(threshold=65)
        logger.info("Fixed auto search initialized with enhanced electronic music support")
        enhance_auto_search_with_parser(self)
        
    def _parse_match_line(self, line):
        """Parse a line from a match file."""
        line = line.strip()
        
        if not line or line.startswith('#'):
            return None
        
        original_line = line
        
        # Try to parse artist and title with common separators
        separators = [' - ', ' – ', ': ', ' : ', '_-_', ',', ' | ', ' / ']
        
        artist = ""
        title = ""
        
        for separator in separators:
            if separator in line:
                parts = line.split(separator, 1)
                if len(parts) == 2:
                    artist = parts[0].strip()
                    title = parts[1].strip()
                    break
        
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
    
    def clean_playlist_entry(self, text):
        """Clean playlist entries for better matching."""
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # Remove feat./featuring variations
        cleaned = re.sub(r'\s+(feat\.?|featuring|ft\.?)\s+[^-\(]+', '', cleaned, flags=re.IGNORECASE)
        
        # Remove remix/version info
        remix_patterns = [
            r'\s*-\s*[^-]*remix[^-]*$',
            r'\s*-\s*[^-]*mix[^-]*$', 
            r'\s*-\s*[^-]*edit[^-]*$',
            r'\s*-\s*[^-]*version[^-]*$',
            r'\s*-\s*original[^-]*$',
            r'\s*-\s*radio[^-]*$',
            r'\s*\([^)]*remix[^)]*\)\s*$',
            r'\s*\([^)]*mix[^)]*\)\s*$',
            r'\s*\([^)]*edit[^)]*\)\s*$',
        ]
        
        original_cleaned = cleaned
        for pattern in remix_patterns:
            test_cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
            if len(test_cleaned) >= len(original_cleaned) * 0.4:
                cleaned = test_cleaned
        
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def generate_search_variants(self, original_line):
        """Generate multiple search variants from a playlist entry."""
        variants = []
        
        # 1. Original line
        variants.append(original_line)
        
        # 2. Cleaned version
        cleaned = self.clean_playlist_entry(original_line)
        if cleaned != original_line and len(cleaned) >= 5:
            variants.append(cleaned)
        
        # 3. Without parentheses
        no_parens = re.sub(r'\s*\([^)]*\)', '', original_line).strip()
        if no_parens != original_line and len(no_parens) >= 5:
            variants.append(no_parens)
        
        # 4. Title only (after dash)
        if ' - ' in original_line:
            title_part = original_line.split(' - ', 1)[1].strip()
            if len(title_part) >= 5:
                variants.append(title_part)
        
        # 5. Without "The"
        for variant in variants[:]:
            if variant.lower().startswith('the '):
                no_the = variant[4:].strip()
                if no_the and len(no_the) >= 3:
                    variants.append(no_the)
        
        # Remove duplicates
        unique_variants = []
        for variant in variants:
            if variant and len(variant) >= 3 and variant not in unique_variants:
                unique_variants.append(variant)
        
        return unique_variants[:8]
    
    def _find_matches_general_query(self, query):
        """Find matches using general query approach with enhanced filename handling."""
        if not query or len(query.strip()) < 3:
            return []
        
        logger.debug(f"Enhanced general query search for: '{query}'")
        
        # Get files with pre-filtering for large collections
        cache_stats = self.cache_manager.get_cache_stats()
        total_files = cache_stats.get('total_files', 0)
        
        if total_files > 10000:
            query_words = self._extract_query_words(query)
            if query_words and len(query_words) >= 2:
                try:
                    candidate_files = self.cache_manager.get_candidate_files(
                        artist_words=query_words[:3],
                        title_words=query_words[:3],
                        limit=5000
                    )
                    logger.debug(f"Pre-filtering: {len(candidate_files)} candidates from {total_files} files")
                    
                    if len(candidate_files) < 50 and total_files > 1000:
                        logger.debug("Too few candidates, using all files")
                        candidate_files = self.cache_manager.get_all_files()
                except Exception as e:
                    logger.warning(f"Pre-filtering failed, using all files: {str(e)}")
                    candidate_files = self.cache_manager.get_all_files()
            else:
                candidate_files = self.cache_manager.get_all_files()
        else:
            candidate_files = self.cache_manager.get_all_files()
        
        matches = []
        
        for file_metadata in candidate_files:
            # Test against multiple fields with enhanced filename handling
            artist = file_metadata.get('artist', '')
            title = file_metadata.get('title', '')
            album = file_metadata.get('album', '')
            filename = file_metadata.get('filename', '')
            
            # Calculate match scores - filename score uses enhanced method
            artist_score = self.string_matcher.match_strings(query, artist) if artist else 0
            title_score = self.string_matcher.match_strings(query, title) if title else 0
            album_score = self.string_matcher.match_strings(query, album) if album else 0
            filename_score = self.string_matcher.match_against_filename(query, filename) if filename else 0
            
            # Use highest score
            max_score = max(artist_score, title_score, album_score, filename_score)
            
            if max_score >= self.string_matcher.threshold:
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
                
                match_result.update(file_metadata)
                matches.append(match_result)
        
        # Sort by combined score
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        limited_matches = matches[:50]
        
        logger.debug(f"Enhanced general query found {len(matches)} matches (showing top {len(limited_matches)})")
        
        return limited_matches
    
    def _extract_query_words(self, query):
        """Extract meaningful words from query for pre-filtering."""
        if not query:
            return []
        
        cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
        words = cleaned.split()
        
        stop_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'is', 'are', 'was', 'were'}
        meaningful_words = [w for w in words if len(w) >= 3 and w not in stop_words]
        
        return meaningful_words
    
    def _find_matches_for_entry(self, parsed_info):
        """Find matches for a single entry using multi-variant strategy."""
        original_line = parsed_info['original_line']
        artist = parsed_info['artist']
        title = parsed_info['title']
        
        logger.debug(f"Processing: '{original_line}'")
        
        # Generate multiple search variants
        search_variants = self.generate_search_variants(original_line)
        
        best_matches = []
        best_score = 0
        
        # Try each variant with general query
        for i, variant in enumerate(search_variants):
            logger.debug(f"Trying variant {i+1}: '{variant}'")
            
            variant_matches = self._find_matches_general_query(variant)
            
            if variant_matches:
                current_best_score = variant_matches[0].get('combined_score', 0)
                
                if current_best_score > best_score:
                    best_matches = variant_matches
                    best_score = current_best_score
                    logger.debug(f"Variant '{variant}' found better matches (score: {current_best_score:.1f})")
                
                # If we found excellent matches, stop here
                if current_best_score >= 85:
                    logger.debug(f"Found excellent matches with variant '{variant}', stopping search")
                    break
        
        # Fallback: try individual components
        if best_score < 70 and (artist or title):
            logger.debug("Trying individual artist/title components")
            
            if artist and len(artist) >= 4:
                artist_matches = self._find_matches_general_query(artist)
                if artist_matches and artist_matches[0].get('combined_score', 0) > best_score:
                    best_matches = artist_matches
                    best_score = artist_matches[0].get('combined_score', 0)
                    logger.debug(f"Artist-only search found better matches")
            
            if title and len(title) >= 4:
                title_matches = self._find_matches_general_query(title)
                if title_matches and title_matches[0].get('combined_score', 0) > best_score:
                    best_matches = title_matches
                    best_score = title_matches[0].get('combined_score', 0)
                    logger.debug(f"Title-only search found better matches")
        
        if best_matches:
            logger.debug(f"Final result for '{original_line}': {len(best_matches)} matches, "
                        f"best score: {best_score:.1f}")
        else:
            logger.debug(f"No matches found for '{original_line}'")
        
        return best_matches
    
    def process_match_file(self, file_path, show_progress=True):
        """Process a match file using enhanced electronic music support."""
        entries = self._load_match_file(file_path)
        
        if not entries:
            logger.warning(f"No valid entries found in match file: {file_path}")
            return []
        
        cache_stats = self.cache_manager.get_cache_stats()
        logger.info(f"Processing {len(entries)} entries against {cache_stats['total_files']} indexed files")
        logger.info(f"Using enhanced electronic music support with threshold {self.string_matcher.threshold}")
        
        results = []
        total_found = 0
        high_confidence_found = 0
        
        if show_progress:
            progress_bar = tqdm(total=len(entries), desc="Fixed auto search", unit="entry")
        
        for line_num, parsed_info in entries:
            try:
                matches = self._find_matches_for_entry(parsed_info)
                
                result = {
                    'line_num': line_num,
                    'line': parsed_info['original_line'],
                    'artist': parsed_info['artist'],
                    'title': parsed_info['title'],
                    'matches': matches
                }
                results.append(result)
                
                if matches:
                    total_found += 1
                    best_score = matches[0].get('combined_score', 0)
                    if best_score >= 80:
                        high_confidence_found += 1
                    
                    logger.debug(f"'{parsed_info['original_line']}' -> {len(matches)} matches "
                               f"(best: {best_score:.1f}%)")
                else:
                    logger.debug(f"'{parsed_info['original_line']}' -> No matches")
                
            except Exception as e:
                logger.error(f"Error processing '{parsed_info['original_line']}': {str(e)}")
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
        
        # Log final statistics
        total_entries = len(entries)
        success_rate = (total_found / total_entries) * 100 if total_entries > 0 else 0
        high_confidence_rate = (high_confidence_found / total_entries) * 100 if total_entries > 0 else 0
        
        logger.info(f"Fixed auto search completed:")
        logger.info(f"  Total entries: {total_entries}")
        logger.info(f"  Found matches: {total_found} ({success_rate:.1f}%)")
        logger.info(f"  High confidence (80%+): {high_confidence_found} ({high_confidence_rate:.1f}%)")
        
        return results
    
    def save_results(self, results, output_file):
        """Save search results to a file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write("# Fixed Auto Search Results\n")
                file.write("# Enhanced for electronic music with track numbers and underscores\n")
                file.write("# Fixes filename parsing issues like '01-omi_-_the_claim-nrg.mp3'\n\n")
                
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
                            file.write(f"       Score breakdown - Artist: {match.get('artist_score', 0):.1f}, ")
                            file.write(f"Title: {match.get('title_score', 0):.1f}, ")
                            file.write(f"Filename: {match.get('filename_score', 0):.1f}\n")
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
        logger.info(f"Similarity threshold updated to {threshold}")
    
    def debug_search(self, query, max_candidates=10):
        """Debug search function to help diagnose search issues."""
        logger.info(f"=== DEBUG FIXED AUTO SEARCH for '{query}' ===")
        
        # Show how the query gets cleaned
        clean_query = self.string_matcher.clean_string(query)
        logger.info(f"Cleaned query: '{query}' -> '{clean_query}'")
        
        # Generate variants
        variants = self.generate_search_variants(query)
        logger.info(f"Generated {len(variants)} search variants: {variants}")
        
        # Find matches
        matches = self._find_matches_general_query(query)
        
        logger.info(f"General query found {len(matches)} matches")
        
        # Show match details with enhanced info
        for i, match in enumerate(matches[:max_candidates]):
            filename = match.get('filename', 'unknown')
            clean_filename = self.string_matcher.clean_string(filename)
            
            logger.info(f"Match {i+1}: {filename}")
            logger.info(f"  Cleaned filename: '{clean_filename}'")
            logger.info(f"  Score: {match.get('combined_score', 0):.1f}% "
                       f"(A:{match.get('artist_score', 0):.1f}, "
                       f"T:{match.get('title_score', 0):.1f}, "
                       f"F:{match.get('filename_score', 0):.1f})")
        
        return {
            'query': query,
            'clean_query': clean_query,
            'variants': variants,
            'matches_count': len(matches),
            'top_matches': matches[:max_candidates]
        }