#!/usr/bin/env python3
"""
Test script specifically for the track number and underscore fix.
Tests filename cleaning and parsing improvements.

Usage: python test_track_fix.py path/to/your/playlist.txt
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from music_indexer.core.cache_manager import CacheManager
from music_indexer.search.auto_search import AutoSearch, EnhancedStringMatcher
from music_indexer.utils.logger import get_logger

logger = get_logger(log_level="DEBUG")  # Use DEBUG for detailed output

def test_filename_cleaning():
    """Test the enhanced filename cleaning with problematic examples."""
    print("=" * 80)
    print("TESTING FILENAME CLEANING")
    print("=" * 80)
    
    matcher = EnhancedStringMatcher()
    
    # Test cases based on your problematic example
    test_cases = [
        "01-omi_-_the_claim-nrg.mp3",
        "02_artist_-_track_name.mp3", 
        "003-some_artist-track_title-label.flac",
        "a01_dj_name_track_name.mp3",
        "promo_artist_name_song_title.wav",
        "nrg001-artist_name_-_song_title.mp3"
    ]
    
    for i, filename in enumerate(test_cases, 1):
        print(f"{i}. Testing filename: '{filename}'")
        
        # Show cleaning process
        cleaned = matcher.clean_string(filename)
        print(f"   Cleaned: '{cleaned}'")
        
        # Show artist/title extraction
        artist, title = matcher.extract_artist_title_from_cleaned_filename(cleaned)
        print(f"   Parsed: artist='{artist}', title='{title}'")
        
        # Show meaningful words
        words = matcher.extract_meaningful_words(cleaned)
        print(f"   Words: {words}")
        print()

def test_specific_matching_issue(playlist_file_path):
    """Test the specific matching issue you found."""
    print("=" * 80)
    print("TESTING SPECIFIC MATCHING ISSUE")
    print("=" * 80)
    
    # Initialize components
    cache_manager = CacheManager()
    auto_search = AutoSearch(cache_manager)
    
    # Test the specific problematic case
    test_query = "Promo, Omi - Airwalker - OMI Remix"
    problematic_filename = "01-omi_-_the_claim-nrg.mp3"
    
    print(f"Query: '{test_query}'")
    print(f"Problematic filename: '{problematic_filename}'")
    print()
    
    # Show how query gets processed
    print("Query processing:")
    variants = auto_search.generate_search_variants(test_query)
    print(f"  Variants: {variants}")
    
    clean_query = auto_search.string_matcher.clean_string(test_query)
    print(f"  Cleaned query: '{clean_query}'")
    print()
    
    # Show how filename gets processed
    print("Filename processing:")
    clean_filename = auto_search.string_matcher.clean_string(problematic_filename)
    print(f"  Cleaned: '{problematic_filename}' -> '{clean_filename}'")
    
    artist, title = auto_search.string_matcher.extract_artist_title_from_cleaned_filename(clean_filename)
    print(f"  Parsed: artist='{artist}', title='{title}'")
    print()
    
    # Test matching
    print("Matching test:")
    score = auto_search.string_matcher.match_against_filename(test_query, problematic_filename)
    print(f"  Match score: {score:.1f}%")
    
    # Test individual components
    if artist and title:
        artist_score = auto_search.string_matcher.match_strings(clean_query, artist)
        title_score = auto_search.string_matcher.match_strings(clean_query, title)
        combined_score = auto_search.string_matcher.match_strings(clean_query, f"{artist} {title}")
        
        print(f"  Component scores:")
        print(f"    Query vs Artist: {artist_score:.1f}%")
        print(f"    Query vs Title: {title_score:.1f}%")
        print(f"    Query vs Combined: {combined_score:.1f}%")

def test_sample_playlist(playlist_file_path, max_entries=10):
    """Test a sample from the playlist with detailed output."""
    print("=" * 80)
    print("TESTING SAMPLE PLAYLIST")
    print("=" * 80)
    
    if not os.path.exists(playlist_file_path):
        print(f"❌ ERROR: Playlist file not found: {playlist_file_path}")
        return
    
    # Initialize components
    cache_manager = CacheManager()
    auto_search = AutoSearch(cache_manager)
    
    # Check database
    cache_stats = cache_manager.get_cache_stats()
    print(f"Database contains {cache_stats['total_files']} indexed files")
    
    if cache_stats['total_files'] == 0:
        print("❌ ERROR: No files in database!")
        return
    
    # Load test entries
    with open(playlist_file_path, 'r', encoding='utf-8') as f:
        all_entries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    test_entries = all_entries[:max_entries]
    print(f"Testing first {len(test_entries)} entries:")
    print()
    
    for i, entry in enumerate(test_entries, 1):
        print(f"{i}. Query: '{entry}'")
        
        # Parse entry
        parsed = auto_search._parse_match_line(entry)
        if not parsed:
            print("   ❌ Could not parse")
            continue
        
        print(f"   Parsed: artist='{parsed['artist']}', title='{parsed['title']}'")
        
        # Show variants
        variants = auto_search.generate_search_variants(entry)
        print(f"   Variants: {variants}")
        
        # Find matches
        matches = auto_search._find_matches_for_entry(parsed)
        
        if matches:
            best_match = matches[0]
            score = best_match.get('combined_score', 0)
            filename = best_match.get('filename', 'unknown')
            
            # Show the match with detailed scores
            print(f"   ✅ MATCH: {filename} (score: {score:.1f}%)")
            print(f"   Score breakdown: A:{best_match.get('artist_score', 0):.1f}, "
                  f"T:{best_match.get('title_score', 0):.1f}, "
                  f"F:{best_match.get('filename_score', 0):.1f}")
            
            # Show how the matched filename gets processed
            clean_matched = auto_search.string_matcher.clean_string(filename)
            print(f"   Matched file cleaned: '{filename}' -> '{clean_matched}'")
            
            # Check if this looks like a reasonable match
            query_words = set(auto_search.string_matcher.extract_meaningful_words(entry.lower()))
            match_words = set(auto_search.string_matcher.extract_meaningful_words(clean_matched))
            overlap = query_words & match_words
            
            if overlap:
                print(f"   ✓ Common words: {overlap}")
            else:
                print(f"   ⚠️ No common words between '{entry}' and '{clean_matched}'")
                print(f"   Query words: {query_words}")
                print(f"   Match words: {match_words}")
        
        else:
            print(f"   ❌ NO MATCH")
        
        print()

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_track_fix.py <playlist_file>")
        print("\nThis script tests the track number and underscore fixes.")
        print("It will show detailed processing of filenames and matching.")
        return 1
    
    playlist_file = sys.argv[1]
    
    # Run all tests
    test_filename_cleaning()
    test_specific_matching_issue(playlist_file)
    test_sample_playlist(playlist_file, max_entries=10)
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Key improvements in the fixed version:")
    print("✅ Removes track numbers (01-, 001-, etc.) from filenames")
    print("✅ Converts underscores to spaces (_-_ becomes ' - ')")
    print("✅ Better artist/title parsing from electronic music filenames")
    print("✅ Enhanced word extraction that ignores noise")
    print("✅ Improved matching that considers filename structure")
    print()
    print("If the results look better, replace your auto_search.py with the fixed version!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())