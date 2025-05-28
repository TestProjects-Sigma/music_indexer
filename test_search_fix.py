#!/usr/bin/env python3
"""
Test script to compare old vs new search behavior.
Run this to verify the improvements.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from music_indexer.core.cache_manager import CacheManager
from music_indexer.search.string_matcher import StringMatcher
from music_indexer.search.auto_search import AutoSearch
from music_indexer.utils.logger import get_logger

logger = get_logger(log_level="INFO")

def test_problematic_cases():
    """Test the specific cases that were problematic."""
    
    print("=" * 80)
    print("TESTING FIXED SEARCH ALGORITHM")
    print("=" * 80)
    
    # Initialize components
    cache_manager = CacheManager()
    string_matcher = StringMatcher(threshold=75)
    auto_search = AutoSearch(cache_manager, string_matcher)
    
    # Test cases from your problematic list
    test_cases = [
        ("Endymion", "Abduction"),
        ("Party Animals", "Used & Abused - Amnesia Mix"),
        ("The Prophet, DJ Buzz Fuzz", "Go Get Ill - Original Mix"),
        ("Dione", "Pain Til I Die - Remastered"),
        ("Proactive HC", "The definition of hard - Original Mix"),
        ("Meagashira, Endymion", "Who I Am")
    ]
    
    for i, (artist, title) in enumerate(test_cases, 1):
        print(f"\n{i}. TESTING: '{artist} - {title}'")
        print("-" * 60)
        
        # Find matches using the new algorithm
        matches = auto_search._find_matches_for_pair(artist, title)
        
        print(f"Found {len(matches)} matches:")
        
        if matches:
            for j, match in enumerate(matches[:5], 1):  # Show top 5
                score = match.get('combined_score', 0)
                filename = match.get('filename', 'unknown')
                match_artist = match.get('artist', '')
                match_title = match.get('title', '')
                
                print(f"  {j}. {filename}")
                print(f"     Artist: '{match_artist}', Title: '{match_title}'")
                print(f"     Score: {score:.1f}%")
                
                # Validate this looks like a reasonable match
                if score >= 90:
                    search_words = set((artist + " " + title).lower().split())
                    match_words = set((match_artist + " " + match_title + " " + filename).lower().split())
                    overlap = len(search_words & match_words) / len(search_words) if search_words else 0
                    
                    if overlap < 0.3:
                        print(f"     ⚠️  WARNING: High score but low word overlap ({overlap:.1%})")
                    else:
                        print(f"     ✓ Good match (word overlap: {overlap:.1%})")
        else:
            print("  No matches found")
            
            # Let's debug why no matches were found
            print("\n  DEBUG: Checking what went wrong...")
            debug_info = auto_search.debug_search(artist, title, max_candidates=3)
            
            if debug_info['candidates_count'] == 0:
                print("  Issue: Pre-filtering returned no candidates")
            elif debug_info['matches_count'] == 0:
                print("  Issue: String matching failed on candidates")
            else:
                print(f"  Issue: Found {debug_info['matches_count']} matches but below threshold")

def test_false_positive_reduction():
    """Test that we've reduced false positives."""
    
    print("\n" + "=" * 80)
    print("TESTING FALSE POSITIVE REDUCTION")
    print("=" * 80)
    
    # Initialize components
    cache_manager = CacheManager()
    string_matcher = StringMatcher(threshold=75)
    
    # Test cases that should NOT match well
    false_positive_tests = [
        ("Who I Am", "french_gabber_team_-_i_am"),  # This was matching 100% before
        ("Abduction", "extrasensory_perception-abduction"),  # Different artist context
        ("Pain", "twistericals_-_pain"),  # Too generic
    ]
    
    print("\nTesting that these should NOT get high scores:")
    
    for i, (search_term, filename) in enumerate(false_positive_tests, 1):
        print(f"\n{i}. Search: '{search_term}' vs Filename: '{filename}'")
        
        # Create fake metadata
        fake_metadata = {
            'filename': filename,
            'artist': filename.split('-')[0] if '-' in filename else '',
            'title': filename.split('-')[1] if '-' in filename else filename,
            'file_path': f"/fake/path/{filename}"
        }
        
        # Test the match
        match_result = string_matcher.match_song("", search_term, fake_metadata)
        score = match_result['combined_score']
        
        print(f"   Score: {score:.1f}%")
        
        if score >= 85:
            print("   ❌ STILL TOO HIGH - this is a false positive")
        elif score >= 70:
            print("   ⚠️  Moderate score - acceptable")
        else:
            print("   ✅ Low score - good!")

def test_exact_matches():
    """Test that exact matches still work perfectly."""
    
    print("\n" + "=" * 80)
    print("TESTING EXACT MATCHES STILL WORK")
    print("=" * 80)
    
    cache_manager = CacheManager()
    string_matcher = StringMatcher(threshold=75)
    
    # Get a few real files from the database to test
    all_files = cache_manager.get_all_files(limit=50)
    
    if not all_files:
        print("No files in database to test with")
        return
    
    print("\nTesting exact matches with real database files:")
    
    tested = 0
    for file_metadata in all_files:
        if tested >= 5:  # Test only first 5
            break
            
        artist = file_metadata.get('artist', '')
        title = file_metadata.get('title', '')
        filename = file_metadata.get('filename', '')
        
        # Skip files without clear artist/title
        if not artist or not title or len(artist) < 3 or len(title) < 3:
            continue
            
        tested += 1
        print(f"\n{tested}. Testing exact match: '{artist} - {title}'")
        
        # Test matching against itself
        match_result = string_matcher.match_song(artist, title, file_metadata)
        score = match_result['combined_score']
        
        print(f"   File: {filename}")
        print(f"   Score: {score:.1f}%")
        
        if score >= 85:
            print("   ✅ Good exact match score")
        else:
            print("   ❌ PROBLEM: Exact match should score higher")

def main():
    """Main test function."""
    
    # Test the fixed algorithm
    test_problematic_cases()
    test_false_positive_reduction()
    test_exact_matches()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print("\nIf you see mostly ✅ marks, the fixes are working!")
    print("If you see ❌ marks, we need to adjust the algorithm further.")
    print("\nNext steps:")
    print("1. Replace your string_matcher.py with the fixed version")
    print("2. Replace your auto_search.py with the fixed version") 
    print("3. Test with your full playlist file")
    print("4. Check if missing tracks are now found")

if __name__ == "__main__":
    main()