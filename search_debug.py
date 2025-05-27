#!/usr/bin/env python3
"""
Debug script to test and compare manual vs auto search behavior.
Use this to diagnose search issues.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from music_indexer.core.cache_manager import CacheManager
from music_indexer.search.string_matcher import StringMatcher
from music_indexer.search.manual_search import ManualSearch
from music_indexer.search.auto_search import AutoSearch
from music_indexer.utils.logger import get_logger

logger = get_logger(log_level="DEBUG")

def test_search_comparison(search_term, test_as_artist=False, test_as_title=False):
    """
    Test and compare manual vs auto search for a specific term.
    
    Args:
        search_term (str): The term to search for
        test_as_artist (bool): Whether to test as artist search
        test_as_title (bool): Whether to test as title search
    """
    print(f"\n{'='*60}")
    print(f"TESTING SEARCH: '{search_term}'")
    print(f"{'='*60}")
    
    # Initialize components
    cache_manager = CacheManager()
    string_matcher = StringMatcher(threshold=75)
    manual_search = ManualSearch(cache_manager, string_matcher)
    auto_search = AutoSearch(cache_manager, string_matcher)
    
    # Test 1: Manual search with general query
    print(f"\n1. MANUAL SEARCH (General Query)")
    print(f"   Query: '{search_term}'")
    manual_results = manual_search.search(query=search_term)
    print(f"   Results: {len(manual_results)} matches")
    
    for i, result in enumerate(manual_results[:5]):
        score = result.get('combined_score', 0)
        filename = result.get('filename', 'unknown')
        artist = result.get('artist', '')
        title = result.get('title', '')
        print(f"   {i+1}. {filename} (score: {score:.1f}%) - Artist: '{artist}', Title: '{title}'")
    
    # Test 2: Manual search as artist (if requested)
    if test_as_artist:
        print(f"\n2. MANUAL SEARCH (Artist Field)")
        print(f"   Artist: '{search_term}'")
        artist_results = manual_search.search(artist=search_term)
        print(f"   Results: {len(artist_results)} matches")
        
        for i, result in enumerate(artist_results[:5]):
            score = result.get('combined_score', 0)
            filename = result.get('filename', 'unknown')
            artist = result.get('artist', '')
            title = result.get('title', '')
            print(f"   {i+1}. {filename} (score: {score:.1f}%) - Artist: '{artist}', Title: '{title}'")
    
    # Test 3: Manual search as title (if requested)
    if test_as_title:
        print(f"\n3. MANUAL SEARCH (Title Field)")
        print(f"   Title: '{search_term}'")
        title_results = manual_search.search(title=search_term)
        print(f"   Results: {len(title_results)} matches")
        
        for i, result in enumerate(title_results[:5]):
            score = result.get('combined_score', 0)
            filename = result.get('filename', 'unknown')
            artist = result.get('artist', '')
            title = result.get('title', '')
            print(f"   {i+1}. {filename} (score: {score:.1f}%) - Artist: '{artist}', Title: '{title}'")
    
    # Test 4: Auto search (simulate auto search behavior)
    print(f"\n4. AUTO SEARCH SIMULATION")
    print(f"   Searching for: '{search_term}' (as title)")
    
    # Debug the auto search process
    debug_info = auto_search.debug_search("", search_term)  # Empty artist, search_term as title
    
    print(f"   Extracted title words: {debug_info['title_words']}")
    print(f"   Pre-filter candidates: {debug_info['candidates_count']}")
    print(f"   Final matches: {debug_info['matches_count']}")
    
    for i, match in enumerate(debug_info['top_matches']):
        score = match.get('combined_score', 0)
        filename = match.get('filename', 'unknown')
        artist = match.get('artist', '')
        title = match.get('title', '')
        print(f"   {i+1}. {filename} (score: {score:.1f}%) - Artist: '{artist}', Title: '{title}'")
    
    # Test 5: String matching details
    print(f"\n5. STRING MATCHING ANALYSIS")
    
    # Get some files to test against
    all_files = cache_manager.get_all_files(limit=100)  # Test with first 100 files
    
    print(f"   Testing '{search_term}' against sample files:")
    test_matches = []
    
    for file in all_files[:10]:  # Test first 10 files
        filename = file.get('filename', '')
        artist = file.get('artist', '')
        title = file.get('title', '')
        
        # Test different matching methods
        filename_score = string_matcher.match_against_filename(search_term, filename)
        artist_score = string_matcher.match_strings(search_term, artist)
        title_score = string_matcher.match_strings(search_term, title)
        
        max_score = max(filename_score, artist_score, title_score)
        
        if max_score > 0:
            test_matches.append({
                'filename': filename,
                'artist': artist,
                'title': title,
                'filename_score': filename_score,
                'artist_score': artist_score,
                'title_score': title_score,
                'max_score': max_score
            })
    
    # Sort by max score
    test_matches.sort(key=lambda x: x['max_score'], reverse=True)
    
    for i, match in enumerate(test_matches[:5]):
        print(f"   {i+1}. {match['filename']}")
        print(f"      Artist: '{match['artist']}' (score: {match['artist_score']})")
        print(f"      Title: '{match['title']}' (score: {match['title_score']})")
        print(f"      Filename score: {match['filename_score']}")
        print(f"      Max score: {match['max_score']}")

def test_problematic_case():
    """Test the specific problematic case mentioned."""
    print(f"\n{'='*60}")
    print(f"TESTING PROBLEMATIC CASE")
    print(f"{'='*60}")
    
    # The specific case: searching for "Meagashira" but getting "a-hedgehog_affair-oh_my_god_im_a_dj-sour.mp"
    search_term = "Meagashira"
    problem_filename = "a-hedgehog_affair-oh_my_god_im_a_dj-sour.mp3"
    
    string_matcher = StringMatcher(threshold=75)
    
    print(f"Search term: '{search_term}'")
    print(f"Problem filename: '{problem_filename}'")
    print(f"Threshold: {string_matcher.threshold}")
    
    # Test the matching
    score = string_matcher.match_against_filename(search_term, problem_filename)
    print(f"Filename match score: {score}")
    
    # Test regular string matching
    regular_score = string_matcher.match_strings(search_term, problem_filename)
    print(f"Regular string match score: {regular_score}")
    
    # Show the cleaning process
    clean_search = string_matcher.clean_string(search_term)
    clean_filename = string_matcher.clean_string(problem_filename)
    
    print(f"Cleaned search term: '{clean_search}'")
    print(f"Cleaned filename: '{clean_filename}'")
    
    # Test if cleaned search term appears in cleaned filename
    if clean_search in clean_filename:
        print(f"✓ '{clean_search}' found in '{clean_filename}'")
        
        # Find where it appears
        index = clean_filename.find(clean_search)
        print(f"   Found at position {index}")
        print(f"   Context: ...{clean_filename[max(0, index-10):index+len(clean_search)+10]}...")
    else:
        print(f"✗ '{clean_search}' NOT found in '{clean_filename}'")
    
    # Test fuzzy matching scores step by step
    from fuzzywuzzy import fuzz
    
    ratio = fuzz.ratio(clean_search, clean_filename)
    partial_ratio = fuzz.partial_ratio(clean_search, clean_filename)
    token_sort_ratio = fuzz.token_sort_ratio(clean_search, clean_filename)
    token_set_ratio = fuzz.token_set_ratio(clean_search, clean_filename)
    
    print(f"Fuzzy matching scores:")
    print(f"  Ratio: {ratio}")
    print(f"  Partial ratio: {partial_ratio}")
    print(f"  Token sort ratio: {token_sort_ratio}")
    print(f"  Token set ratio: {token_set_ratio}")
    print(f"  Max score: {max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)}")
    
    # Test word extraction
    search_words = string_matcher.extract_key_words(search_term)
    filename_words = string_matcher.extract_key_words(problem_filename)
    
    print(f"Search term words: {search_words}")
    print(f"Filename words: {filename_words}")
    
    # Check for word overlaps
    common_words = set(search_words) & set(filename_words)
    if common_words:
        print(f"Common words found: {common_words}")
    else:
        print("No common words found")
    
    # Test each word individually
    for search_word in search_words:
        for filename_word in filename_words:
            word_score = fuzz.ratio(search_word, filename_word)
            if word_score > 80:
                print(f"High word similarity: '{search_word}' vs '{filename_word}' = {word_score}%")
    
    # Manual analysis - check if any character sequences might be causing the match
    print(f"\nManual analysis:")
    print(f"Search term length: {len(clean_search)}")
    print(f"Filename length: {len(clean_filename)}")
    
    # Check for any suspicious character sequences
    for i in range(len(clean_search) - 1):
        substr = clean_search[i:i+2]
        if substr in clean_filename:
            print(f"2-char sequence '{substr}' found in filename")
    
    for i in range(len(clean_search) - 2):
        substr = clean_search[i:i+3]
        if substr in clean_filename:
            print(f"3-char sequence '{substr}' found in filename")

def test_specific_fuzzy_issue():
    """Test the specific fuzzy matching issue with token_set_ratio."""
    print(f"\n{'='*60}")
    print(f"TESTING FUZZY MATCHING ISSUE")
    print(f"{'='*60}")
    
    from fuzzywuzzy import fuzz
    
    search_term = "Meagashira"
    problem_filename = "a-hedgehog_affair-oh_my_god_im_a_dj-sour.mp3"
    
    string_matcher = StringMatcher(threshold=75)
    clean_search = string_matcher.clean_string(search_term)
    clean_filename = string_matcher.clean_string(problem_filename)
    
    print(f"Clean search: '{clean_search}'")
    print(f"Clean filename: '{clean_filename}'")
    
    # Test token_set_ratio which is likely the culprit
    token_set_score = fuzz.token_set_ratio(clean_search, clean_filename)
    print(f"Token set ratio: {token_set_score}")
    
    # Break down what token_set_ratio does
    search_tokens = set(clean_search.split())
    filename_tokens = set(clean_filename.split())
    
    print(f"Search tokens: {search_tokens}")
    print(f"Filename tokens: {filename_tokens}")
    
    # Check intersection
    intersection = search_tokens & filename_tokens
    print(f"Token intersection: {intersection}")
    
    # This is likely where the issue is - if 'a' from 'Meagashira' matches 'a' from the filename
    # Let's test this theory
    
    # Test with individual characters that might be matching
    if 'a' in clean_search and 'a' in clean_filename:
        print("FOUND THE ISSUE: Both contain 'a' which token_set_ratio might be matching!")
        
        # Test what happens when we have just single character matches
        test_score = fuzz.token_set_ratio('a', 'a hedgehog affair oh my god im a dj sour')
        print(f"Single 'a' vs filename tokens: {test_score}")
        
        # This is the issue! token_set_ratio gives high scores for single character matches

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python search_debug.py <search_term> [--artist] [--title]")
        print("   or: python search_debug.py --test-problem")
        print("   or: python search_debug.py --test-examples")
        print("")
        print("Examples:")
        print("  python search_debug.py Meagashira")
        print("  python search_debug.py Beatles --artist")
        print("  python search_debug.py Yesterday --title")
        print("  python search_debug.py --test-problem")
        print("  python search_debug.py --test-examples")
        return 1
    
    if sys.argv[1] == "--test-problem":
        test_problematic_case()
        return 0
    
    if sys.argv[1] == "--test-examples":
        test_user_examples()
        return 0
    
    search_term = sys.argv[1]
    test_as_artist = "--artist" in sys.argv
    test_as_title = "--title" in sys.argv
    
    test_search_comparison(search_term, test_as_artist, test_as_title)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
