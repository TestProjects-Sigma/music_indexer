#!/usr/bin/env python3
"""
Complete Fixed Optimized Matcher - All fixes in one file
Addresses remix vs original preference and artist matching issues
"""

import os
import sqlite3
import re
from fuzzywuzzy import fuzz
from ..utils.logger import get_logger

logger = get_logger()


class OptimizedMatcher:
    """Complete fixed optimized matcher with proper remix and artist logic."""
    
    def __init__(self, cache_manager):
        """
        Initialize the optimized matcher.
        
        Args:
            cache_manager: CacheManager instance from the main application
        """
        self.cache_manager = cache_manager
        self.min_score = 80
        
        # Electronic music labels from your collection
        self.known_labels = {
            'dps', 'trt', 'pms', 'sq', 'doc', 'vmc', 'dwm', 'apc', 'rfl', 'mim'
        }
        
        logger.info("Complete fixed optimized matcher for electronic music initialized")
        
    def clean_text_for_matching(self, text):
            """Clean text for accurate matching with justify suffix removal."""
            if not text:
                return ""
            
            text = text.lower()
            text = re.sub(r'\s*\([^)]*(?:remix|mix|edit|version|remaster)\)', '', text)
            text = re.sub(r'\s*-\s*[^-]*(?:remix|mix|edit|version|remaster)[^-]*$', '', text)
            
            # NEW: Remove common electronic music suffixes
            text = re.sub(r'[-_]\s*justify\s*$', '', text, flags=re.IGNORECASE)
            text = re.sub(r'[-_]\s*sob\s*$', '', text, flags=re.IGNORECASE)  # Also handles "sob" label
            text = re.sub(r'[-_]\s*nrg\s*$', '', text, flags=re.IGNORECASE)  # Also handles "nrg" label
            
            text = re.sub(r'[^\w\s]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def parse_playlist_entry(self, line):
        """Parse playlist entry with improved remix detection."""
        line = line.strip()
        
        if not line or line.startswith('#'):
            return None
        
        if ' - ' in line:
            parts = line.split(' - ')
            
            if len(parts) == 2:
                artist_part = parts[0].strip()
                title_part = parts[1].strip()
                remix_info = ""
                
                # Check if title_part contains remix info
                remix_keywords = ['remix', 'mix', 'edit', 'version', 'remaster']
                title_lower = title_part.lower()
                
                if any(keyword in title_lower for keyword in remix_keywords):
                    # Title contains remix info - extract it
                    remix_info = title_part
                
            elif len(parts) >= 3:
                artist_part = parts[0].strip()
                
                # Check if last part is remix info
                remix_keywords = ['remix', 'mix', 'edit', 'version', 'remaster']
                last_part = parts[-1].strip().lower()
                
                if any(keyword in last_part for keyword in remix_keywords):
                    title_part = parts[1].strip()
                    remix_info = parts[-1].strip()
                else:
                    title_part = ' - '.join(parts[1:]).strip()
                    remix_info = ""
                    
                    # Check if the combined title contains remix info
                    combined_lower = title_part.lower()
                    if any(keyword in combined_lower for keyword in remix_keywords):
                        remix_info = title_part
            
            # Handle comma-separated artists
            if ',' in artist_part:
                primary_artist = artist_part.split(',')[0].strip()
                all_artists = [a.strip() for a in artist_part.split(',')]
            else:
                primary_artist = artist_part
                all_artists = [artist_part]
            
            # Create artist variations for better matching
            artist_variations = [primary_artist]
            
            # Add lowercase version
            if primary_artist.lower() != primary_artist:
                artist_variations.append(primary_artist.lower())
            
            # Handle "Unknown" variations
            if primary_artist.lower() in ['unknown', 'various', 'va', 'various artists']:
                artist_variations.extend(['unknown', 'promo', 'various', 'va'])
            
            # Handle "Promo" variations  
            if primary_artist.lower() == 'promo':
                artist_variations.extend(['unknown', 'promo', 'various'])
            
            # Extract clean title (without remix info for base matching)
            clean_title = title_part
            if remix_info and remix_info != title_part:
                # Remix info was in separate part
                clean_title = title_part
            elif remix_info:
                # Remix info is embedded in title - try to extract clean title
                clean_title = self.extract_clean_title_from_remix(title_part)
            
            return {
                'artist': primary_artist,
                'all_artists': all_artists,
                'artist_variations': artist_variations,
                'title': title_part,  # Keep original title
                'clean_title': clean_title,  # Clean title for base matching
                'remix_info': remix_info,
                'original': line
            }
        else:
            return {
                'artist': '',
                'all_artists': [],
                'artist_variations': [''],
                'title': line,
                'clean_title': line,
                'remix_info': '',
                'original': line
            }
    
    def extract_clean_title_from_remix(self, title_with_remix):
        """Extract clean title from a title that contains remix info."""
        # Patterns to remove remix info
        patterns = [
            r'\s*-\s*[^-]*(?:remix|mix|edit|version|remaster)[^-]*$',  # "Title - Artist Remix"
            r'\s*\([^)]*(?:remix|mix|edit|version|remaster)[^)]*\)\s*$',  # "Title (Remix Info)"
            r'\s+(?:remix|mix|edit|version|remaster).*$',  # "Title Remix Info"
        ]
        
        clean_title = title_with_remix
        for pattern in patterns:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
        
        return clean_title.strip()
    
    def has_remix_info(self, parsed_entry):
        """Check if the search entry contains remix information."""
        remix_info = parsed_entry.get('remix_info', '')
        title = parsed_entry.get('title', '')
        
        # Direct remix info
        if remix_info and remix_info.strip():
            return True
        
        # Check for remix keywords in title
        remix_keywords = ['remix', 'mix', 'edit', 'version', 'remaster']
        title_lower = title.lower()
        
        return any(keyword in title_lower for keyword in remix_keywords)
    
    def extract_remix_terms(self, parsed_entry):
        """Extract remix-related terms for matching."""
        remix_terms = []
        
        remix_info = parsed_entry.get('remix_info', '')
        title = parsed_entry.get('title', '')
        
        # From explicit remix info
        if remix_info:
            remix_terms.extend(remix_info.lower().split())
        
        # From title if it contains remix info
        if self.has_remix_info(parsed_entry):
            title_lower = title.lower()
            
            # Extract words around remix keywords
            remix_keywords = ['remix', 'mix', 'edit', 'version', 'remaster']
            for keyword in remix_keywords:
                if keyword in title_lower:
                    # Find the remix phrase
                    if '(' in title and ')' in title:
                        # Extract from parentheses
                        paren_match = re.search(r'\(([^)]*' + keyword + r'[^)]*)\)', title, re.IGNORECASE)
                        if paren_match:
                            remix_terms.extend(paren_match.group(1).lower().split())
                    
                    # Extract from dash-separated part
                    dash_parts = title.split(' - ')
                    for part in dash_parts:
                        if keyword in part.lower():
                            remix_terms.extend(part.lower().split())
        
        # Clean and filter terms
        cleaned_terms = []
        for term in remix_terms:
            term = re.sub(r'[^\w]', '', term)  # Remove punctuation
            if len(term) > 2:  # Skip very short terms
                cleaned_terms.append(term)
        
        return list(set(cleaned_terms))  # Remove duplicates
    
    def file_appears_to_be_remix(self, filename, db_title):
        """Check if a file appears to be a remix version."""
        remix_indicators = ['remix', 'mix', 'edit', 'version', 'remaster']
        
        # Check filename
        filename_lower = filename.lower()
        filename_has_remix = any(indicator in filename_lower for indicator in remix_indicators)
        
        # Check title
        title_lower = (db_title or '').lower()
        title_has_remix = any(indicator in title_lower for indicator in remix_indicators)
        
        # Check for parentheses with remix info
        paren_remix_pattern = r'\([^)]*(?:remix|mix|edit|version)[^)]*\)'
        filename_has_paren_remix = bool(re.search(paren_remix_pattern, filename, re.IGNORECASE))
        title_has_paren_remix = bool(re.search(paren_remix_pattern, db_title or '', re.IGNORECASE))
        
        return (filename_has_remix or title_has_remix or 
                filename_has_paren_remix or title_has_paren_remix)
    
    def calculate_remix_match_score(self, search_remix_terms, filename, db_title):
        """Calculate how well the file's remix info matches the search remix terms."""
        if not search_remix_terms:
            return 0
        
        # Extract remix terms from the file
        file_text = f"{filename} {db_title or ''}".lower()
        
        matches = 0
        for term in search_remix_terms:
            if term in file_text:
                matches += 1
        
        # Calculate percentage match
        if len(search_remix_terms) > 0:
            return (matches / len(search_remix_terms)) * 100
        
        return 0
    
    def enhanced_artist_match_score(self, search_artist, search_variations, db_artist):
        """Enhanced artist matching with variations."""
        if not search_artist or not db_artist:
            return 0
        
        # Direct match
        clean_search = self.clean_text_for_matching(search_artist)
        clean_db = self.clean_text_for_matching(db_artist)
        
        if clean_search == clean_db:
            return 100  # Perfect match
        
        # Try variations
        best_score = 0
        for variation in search_variations:
            clean_variation = self.clean_text_for_matching(variation)
            if clean_variation == clean_db:
                best_score = max(best_score, 95)  # Very good variation match
            else:
                # Fuzzy match with variation
                score = fuzz.ratio(clean_variation, clean_db)
                best_score = max(best_score, score)
        
        return best_score
    
    def conservative_match_score(self, search_title, db_title, search_artist="", db_artist="", search_variations=None):
        """Conservative matching with artist variations."""
        clean_search_title = self.clean_text_for_matching(search_title)
        clean_db_title = self.clean_text_for_matching(db_title)
        clean_search_artist = self.clean_text_for_matching(search_artist)
        clean_db_artist = self.clean_text_for_matching(db_artist)
        
        # Title matching
        title_score = 0
        if clean_search_title and clean_db_title:
            title_score = fuzz.ratio(clean_search_title, clean_db_title)
            
            if len(clean_search_title) <= 8 or len(clean_db_title) <= 8:
                if title_score < 90:
                    title_score = 0
            else:
                if title_score < 80:
                    title_score = 0
        
        # Enhanced Artist matching with variations
        artist_score = 0
        if search_artist and db_artist:
            if search_variations:
                artist_score = self.enhanced_artist_match_score(search_artist, search_variations, db_artist)
            else:
                artist_score = fuzz.ratio(clean_search_artist, clean_db_artist)
            
            if artist_score < 80:
                artist_score = 0
        elif not search_artist:
            artist_score = 60
        
        # Combined score
        if search_artist:
            combined_score = (title_score * 0.7) + (artist_score * 0.3)
        else:
            combined_score = title_score
        
        # Word overlap validation
        if combined_score >= 85:
            search_words = set(clean_search_title.split())
            db_words = set(clean_db_title.split())
            
            if search_words and db_words:
                overlap = len(search_words & db_words) / len(search_words)
                if overlap < 0.4:
                    combined_score = min(75, combined_score)
        
        return combined_score
    
    def calculate_optimized_ranking_bonus(self, search_entry, file_data):
        """Improved ranking bonus with better remix detection."""
        file_path, filename, db_artist, db_title, format_type, duration, bitrate = file_data
        
        search_artist = search_entry['artist']
        all_artists = search_entry['all_artists']
        search_variations = search_entry.get('artist_variations', [search_artist])
        
        # Improved remix detection
        has_remix = self.has_remix_info(search_entry)
        remix_terms = self.extract_remix_terms(search_entry) if has_remix else []
        
        bonus = 0
        bonus_reasons = []
        
        # BONUS 1: Enhanced artist match with variations (+5-8 points)
        if search_artist and db_artist:
            artist_score = self.enhanced_artist_match_score(search_artist, search_variations, db_artist)
            if artist_score >= 95:
                bonus += 8
                bonus_reasons.append("perfect_artist_variation")
            elif artist_score >= 90:
                bonus += 5
                bonus_reasons.append("exact_artist")
        
        # BONUS 2: Multi-artist collaboration match (+8 points)
        if len(all_artists) > 1 and (db_artist or filename):
            clean_filename = self.clean_text_for_matching(filename)
            clean_db_artist = self.clean_text_for_matching(db_artist or '')
            
            artists_found = 0
            for artist in all_artists:
                clean_artist = self.clean_text_for_matching(artist)
                if (clean_artist in clean_filename or 
                    clean_artist in clean_db_artist or
                    any(word in clean_filename for word in clean_artist.split() if len(word) > 2)):
                    artists_found += 1
            
            if artists_found >= 2:
                bonus += 8
                bonus_reasons.append("multi_artist_match")
        
        # BONUS 3: Improved Remix/Original preference logic
        if has_remix and remix_terms:
            # Search HAS remix info - prefer matching remix versions
            file_has_remix = self.file_appears_to_be_remix(filename, db_title)
            
            if file_has_remix:
                # This is a remix file - check if it matches the searched remix
                remix_match_score = self.calculate_remix_match_score(remix_terms, filename, db_title)
                
                if remix_match_score >= 90:
                    bonus += 25  # Perfect remix match
                    bonus_reasons.append("perfect_remix_match")
                elif remix_match_score >= 70:
                    bonus += 15  # Good remix match
                    bonus_reasons.append("good_remix_match")
                elif remix_match_score >= 50:
                    bonus += 8   # Partial remix match
                    bonus_reasons.append("partial_remix_match")
                else:
                    # Wrong remix type
                    bonus -= 5
                    bonus_reasons.append("wrong_remix_type")
            else:
                # This is NOT a remix, but search wants remix - penalize
                bonus -= 10
                bonus_reasons.append("original_when_remix_wanted")
        
        else:
            # Search has NO remix info - prefer ORIGINAL versions
            file_has_remix = self.file_appears_to_be_remix(filename, db_title)
            
            if file_has_remix:
                # This appears to be a remix - PENALIZE when search wants original
                bonus -= 10
                bonus_reasons.append("remix_penalty")
            else:
                # This appears to be an original - REWARD when search wants original
                bonus += 8
                bonus_reasons.append("original_preferred")
        
        # BONUS 4: Format quality (+1-3 points)
        if format_type:
            fmt = format_type.lower()
            if fmt in ['flac']:
                bonus += 3
                bonus_reasons.append("format_flac")
            elif fmt in ['wav']:
                bonus += 2
                bonus_reasons.append("format_wav")
            elif fmt == 'mp3':
                bonus += 1
                bonus_reasons.append("format_mp3")
        
        # BONUS 5: Higher bitrate (+1-2 points)
        if bitrate:
            try:
                br = int(bitrate)
                if br >= 320:
                    bonus += 2
                    bonus_reasons.append("high_bitrate")
                elif br >= 256:
                    bonus += 1
                    bonus_reasons.append("med_bitrate")
            except:
                pass
        
        return bonus, bonus_reasons
    
    def search_for_entry(self, parsed_entry):
        """Search with improved remix-aware matching."""
        if not parsed_entry:
            return []
        
        # Get all files from database using cache manager
        all_files = self.cache_manager.get_all_files()
        
        matches = []
        search_artist = parsed_entry['artist']
        search_title = parsed_entry['title']
        clean_search_title = parsed_entry.get('clean_title', search_title)
        has_remix = self.has_remix_info(parsed_entry)
        search_variations = parsed_entry.get('artist_variations', [search_artist])
        
        logger.debug(f"Improved search for: Artist='{search_artist}', Title='{search_title}', "
                    f"CleanTitle='{clean_search_title}', HasRemix={has_remix}")
        
        for file_metadata in all_files:
            file_path = file_metadata.get('file_path', '')
            filename = file_metadata.get('filename', '')
            db_artist = file_metadata.get('artist', '')
            db_title = file_metadata.get('title', '')
            format_type = file_metadata.get('format', '')
            duration = file_metadata.get('duration', 0)
            bitrate = file_metadata.get('bitrate', 0)
            
            file_data = (file_path, filename, db_artist, db_title, format_type, duration, bitrate)
            
            # Calculate base scores using clean title for better matching
            base_scores = []
            
            # Strategy 1: Artist + Clean Title matching (with variations)
            if search_artist:
                score1 = self.conservative_match_score(
                    clean_search_title, db_title, search_artist, db_artist, search_variations
                )
                if score1 >= self.min_score:
                    base_scores.append(('artist_title', score1))
            
            # Strategy 2: Clean Title-only matching
            score2 = self.conservative_match_score(clean_search_title, db_title)
            if score2 >= self.min_score:
                base_scores.append(('title_only', score2))
            
            # Strategy 3: Full title matching (for remix-specific matching)
            if has_remix and search_title != clean_search_title:
                score3 = self.conservative_match_score(search_title, db_title)
                if score3 >= self.min_score:
                    base_scores.append(('full_title_remix', score3))
            
            # Strategy 4: Filename matching
            clean_filename = self.clean_text_for_matching(filename)
            clean_search_for_filename = self.clean_text_for_matching(clean_search_title)
            if clean_filename and clean_search_for_filename:
                filename_score = fuzz.partial_ratio(clean_search_for_filename, clean_filename)
                if filename_score >= 85:
                    base_scores.append(('filename', filename_score))
            
            # Take the best base score
            if base_scores:
                best_strategy, best_base_score = max(base_scores, key=lambda x: x[1])
                
                # Apply improved ranking bonus
                ranking_bonus, bonus_reasons = self.calculate_optimized_ranking_bonus(parsed_entry, file_data)
                
                # Strategy preference bonus
                strategy_bonus = 0
                if best_strategy == 'artist_title':
                    strategy_bonus = 3
                elif best_strategy == 'full_title_remix':
                    strategy_bonus = 5  # Higher bonus for full remix title match
                elif best_strategy == 'title_only':
                    strategy_bonus = 1
                
                final_score = best_base_score + ranking_bonus + strategy_bonus
                final_score = min(150, final_score)
                
                strategy_info = best_strategy
                if bonus_reasons:
                    strategy_info += f"+{'+'.join(bonus_reasons)}"
                
                matches.append({
                    'file_path': file_path,
                    'filename': filename,
                    'artist': db_artist,
                    'title': db_title,
                    'format': format_type,
                    'duration': duration,
                    'bitrate': bitrate,
                    'match_score': final_score,
                    'base_score': best_base_score,
                    'ranking_bonus': ranking_bonus + strategy_bonus,
                    'strategy': strategy_info,
                    'combined_score': final_score
                })
        
        # Sort by final score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        top_matches = matches[:10]
        
        logger.debug(f"Improved search found {len(matches)} matches (showing top {len(top_matches)})")
        for i, match in enumerate(top_matches, 1):
            remix_indicator = "🎵" if self.file_appears_to_be_remix(match['filename'], match['title']) else "🎶"
            logger.debug(f"  {i}. {remix_indicator} {match['filename']} - Score: {match['match_score']:.1f}% ({match['strategy']})")
        
        return top_matches
    
    def process_match_file(self, file_path, show_progress=True):
        """Process a match file using the complete fixed optimized matcher."""
        if not os.path.exists(file_path):
            logger.error(f"Match file not found: {file_path}")
            return []
        
        logger.info(f"Processing match file with complete fixed optimized matcher: {file_path}")
        
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    parsed_entry = self.parse_playlist_entry(line)
                    
                    if parsed_entry:
                        matches = self.search_for_entry(parsed_entry)
                        
                        result = {
                            'line_num': line_num,
                            'line': parsed_entry['original'],
                            'artist': parsed_entry['artist'],
                            'title': parsed_entry['title'],
                            'matches': matches
                        }
                        results.append(result)
                        
                        if matches:
                            best_score = matches[0]['match_score']
                            strategy = matches[0]['strategy']
                            logger.debug(f"Line {line_num}: '{parsed_entry['original']}' -> "
                                       f"{len(matches)} matches (best: {best_score:.1f}% - {strategy})")
                        else:
                            logger.debug(f"Line {line_num}: '{parsed_entry['original']}' -> No matches")
        
        except Exception as e:
            logger.error(f"Error processing match file: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
        
        total_entries = len(results)
        found_entries = sum(1 for r in results if r['matches'])
        
        logger.info(f"Complete fixed optimized matching completed: {found_entries}/{total_entries} entries found matches")
        
        return results