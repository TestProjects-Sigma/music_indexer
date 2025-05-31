#!/usr/bin/env python3
"""
Final Optimized Matcher - Perfect Ranking for Electronic Music
Integrated version for the Music Indexer application
"""

import os
import sqlite3
import re
from fuzzywuzzy import fuzz
from ..utils.logger import get_logger

logger = get_logger()


class OptimizedMatcher:
    """Optimized matcher with perfect ranking for electronic music playlists."""
    
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
        
        logger.info("Optimized matcher for electronic music initialized")
        
    def clean_text_for_matching(self, text):
        """Clean text for accurate matching."""
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'\s*\([^)]*(?:remix|mix|edit|version|remaster)\)', '', text)
        text = re.sub(r'\s*-\s*[^-]*(?:remix|mix|edit|version|remaster)[^-]*$', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_playlist_entry(self, line):
        """Parse playlist entry."""
        line = line.strip()
        
        if not line or line.startswith('#'):
            return None
        
        if ' - ' in line:
            parts = line.split(' - ')
            
            if len(parts) == 2:
                artist_part = parts[0].strip()
                title_part = parts[1].strip()
                remix_info = ""
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
            
            # Handle comma-separated artists
            if ',' in artist_part:
                primary_artist = artist_part.split(',')[0].strip()
                all_artists = [a.strip() for a in artist_part.split(',')]
            else:
                primary_artist = artist_part
                all_artists = [artist_part]
            
            return {
                'artist': primary_artist,
                'all_artists': all_artists,
                'title': title_part,
                'remix_info': remix_info,
                'original': line
            }
        else:
            return {
                'artist': '',
                'all_artists': [],
                'title': line,
                'remix_info': '',
                'original': line
            }
    
    def conservative_match_score(self, search_title, db_title, search_artist="", db_artist=""):
        """Conservative matching core algorithm."""
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
        
        # Artist matching
        artist_score = 0
        if clean_search_artist and clean_db_artist:
            artist_score = fuzz.ratio(clean_search_artist, clean_db_artist)
            if artist_score < 80:
                artist_score = 0
        elif not clean_search_artist:
            artist_score = 60
        
        # Combined score
        if clean_search_artist:
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
        """Calculate optimized ranking bonus with better remix detection."""
        file_path, filename, db_artist, db_title, format_type, duration, bitrate = file_data
        
        search_artist = search_entry['artist']
        search_remix = search_entry['remix_info']
        all_artists = search_entry['all_artists']
        
        bonus = 0
        bonus_reasons = []
        
        # BONUS 1: Exact artist match (+5 points)
        if search_artist and db_artist:
            clean_search_artist = self.clean_text_for_matching(search_artist)
            clean_db_artist = self.clean_text_for_matching(db_artist)
            if clean_search_artist == clean_db_artist:
                bonus += 5
                bonus_reasons.append("exact_artist")
        
        # BONUS 2: Multi-artist collaboration match (+8 points)
        if len(all_artists) > 1 and (db_artist or filename):
            clean_filename = self.clean_text_for_matching(filename)
            clean_db_artist = self.clean_text_for_matching(db_artist or '')
            
            # Check if multiple artists appear in filename or db_artist
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
        
        # BONUS 3: Remix info match (ENHANCED - Higher bonus)
        if search_remix:
            clean_search_remix = self.clean_text_for_matching(search_remix)
            clean_filename = self.clean_text_for_matching(filename)
            clean_title = self.clean_text_for_matching(db_title or '')
            
            # More sophisticated remix matching
            remix_words = clean_search_remix.split()
            filename_words = clean_filename.split()
            title_words = clean_title.split()
            
            # Check for exact remix phrase match
            if clean_search_remix in clean_filename or clean_search_remix in clean_title:
                bonus += 20  # INCREASED: Perfect remix match gets high bonus
                bonus_reasons.append("perfect_remix_match")
            else:
                # Check for partial remix word matches
                remix_word_matches = 0
                for remix_word in remix_words:
                    if len(remix_word) > 2:  # Skip short words
                        if (remix_word in filename_words or 
                            remix_word in title_words or
                            any(fuzz.ratio(remix_word, fw) >= 85 for fw in filename_words)):
                            remix_word_matches += 1
                
                if remix_word_matches >= len(remix_words) * 0.7:  # 70% of remix words match
                    bonus += 15
                    bonus_reasons.append("remix_partial_match")
                elif remix_word_matches > 0:
                    bonus += 8
                    bonus_reasons.append("remix_words_match")
        
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
        """Search with optimized ranking."""
        if not parsed_entry:
            return []
        
        # Get all files from database using cache manager
        all_files = self.cache_manager.get_all_files()
        
        matches = []
        search_artist = parsed_entry['artist']
        search_title = parsed_entry['title']
        search_remix = parsed_entry['remix_info']
        
        logger.debug(f"Optimized search for: Artist='{search_artist}', Title='{search_title}', Remix='{search_remix}'")
        
        for file_metadata in all_files:
            file_path = file_metadata.get('file_path', '')
            filename = file_metadata.get('filename', '')
            db_artist = file_metadata.get('artist', '')
            db_title = file_metadata.get('title', '')
            format_type = file_metadata.get('format', '')
            duration = file_metadata.get('duration', 0)
            bitrate = file_metadata.get('bitrate', 0)
            
            file_data = (file_path, filename, db_artist, db_title, format_type, duration, bitrate)
            
            # Calculate base scores
            base_scores = []
            
            # Strategy 1: Artist + Title matching
            if search_artist:
                score1 = self.conservative_match_score(search_title, db_title, search_artist, db_artist)
                if score1 >= self.min_score:
                    base_scores.append(('artist_title', score1))
            
            # Strategy 2: Title-only matching
            score2 = self.conservative_match_score(search_title, db_title)
            if score2 >= self.min_score:
                base_scores.append(('title_only', score2))
            
            # Strategy 3: Filename matching
            clean_filename = self.clean_text_for_matching(filename)
            clean_search = self.clean_text_for_matching(search_title)
            if clean_filename and clean_search:
                filename_score = fuzz.partial_ratio(clean_search, clean_filename)
                if filename_score >= 85:
                    base_scores.append(('filename', filename_score))
            
            # Take the best base score
            if base_scores:
                best_strategy, best_base_score = max(base_scores, key=lambda x: x[1])
                
                # Apply optimized ranking bonus
                ranking_bonus, bonus_reasons = self.calculate_optimized_ranking_bonus(parsed_entry, file_data)
                
                # Strategy preference bonus
                strategy_bonus = 0
                if best_strategy == 'artist_title':
                    strategy_bonus = 3  # Prefer exact artist+title matches
                elif best_strategy == 'title_only':
                    strategy_bonus = 1  # Neutral
                # filename gets no strategy bonus
                
                final_score = best_base_score + ranking_bonus + strategy_bonus
                
                # Cap at reasonable maximum
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
                    'combined_score': final_score  # For compatibility with existing code
                })
        
        # Sort by final score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        top_matches = matches[:10]  # Return top 10 matches
        
        logger.debug(f"Optimized search found {len(matches)} matches (showing top {len(top_matches)})")
        for i, match in enumerate(top_matches, 1):
            logger.debug(f"  {i}. {match['filename']} - Score: {match['match_score']:.1f}%")
        
        return top_matches
    
    def process_match_file(self, file_path, show_progress=True):
        """
        Process a match file using the optimized matcher.
        
        Args:
            file_path (str): Path to the playlist file
            show_progress (bool): Whether to show progress (unused in this version)
        
        Returns:
            list: List of results compatible with the existing GUI
        """
        if not os.path.exists(file_path):
            logger.error(f"Match file not found: {file_path}")
            return []
        
        logger.info(f"Processing match file with optimized matcher: {file_path}")
        
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
                            logger.debug(f"Line {line_num}: '{parsed_entry['original']}' -> "
                                       f"{len(matches)} matches (best: {best_score:.1f}%)")
                        else:
                            logger.debug(f"Line {line_num}: '{parsed_entry['original']}' -> No matches")
        
        except Exception as e:
            logger.error(f"Error processing match file: {str(e)}")
            return []
        
        total_entries = len(results)
        found_entries = sum(1 for r in results if r['matches'])
        
        logger.info(f"Optimized matching completed: {found_entries}/{total_entries} entries found matches")
        
        return results