#!/usr/bin/env python3
"""
Debug script to find the real problem with your search.
Run this to diagnose what's going wrong.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from music_indexer.core.cache_manager import CacheManager
from music_indexer.search.string_matcher import StringMatcher
from music_indexer.search.manual_search import ManualSearch

def test_basic_search():
    """Test basic search functionality to find the problem."""
    
    print("🔍 DEBUGGING SEARCH SYSTEM")
    print("=" * 50)
    
    # Initialize components
    try:
        cache_manager = CacheManager()
        string_matcher = StringMatcher(threshold=75)
        manual_search = ManualSearch(cache_manager, string_matcher)
        print("✅ Components initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        return
    
    # Test 1: Check database content
    print("\n1. CHECKING DATABASE CONTENT:")
    try:
        all_files = cache_manager.get_all_files(limit=10)
        print(f"   Database has files: {len(all_files)}")
        
        if all_files:
            print("   Sample files:")
            for i, file in enumerate(all_files[:5]):
                artist = file.get('artist', 'NO ARTIST')
                title = file.get('title', 'NO TITLE')
                filename = file.get('filename', 'NO FILENAME')
                print(f"     {i+1}. Artist: '{artist}' | Title: '{title}' | File: {filename}")
        else:
            print("   ❌ NO FILES IN DATABASE!")
            return
            
    except Exception as e:
        print(f"   ❌ Error accessing database: {e}")
        return
    
    # Test 2: Test string matching directly
    print("\n2. TESTING STRING MATCHING:")
    test_cases = [
        ("Endymion", "Endymion", "Should be 100%"),
        ("Beatles", "The Beatles", "Should be high"),
        ("Yesterday", "Yesterday", "Should be 100%"),
        ("RandomStuff", "Totally Different", "Should be low"),
        ("Meagashira", "a-hedgehog_affair-oh_my_god_im_a_dj-sour", "Should be low")
    ]
    
    for search, target, expected in test_cases:
        score = string_matcher.match_strings(search, target)
        print(f"   '{search}' vs '{target}': {score}% ({expected})")
    
    # Test 3: Test manual search with simple query
    print("\n3. TESTING MANUAL SEARCH:")
    try:
        # Get a real artist from the database
        if all_files:
            real_artist = all_files[0].get('artist', '')
            if real_artist and len(real_artist) > 2:
                print(f"   Searching for artist: '{real_artist}'")
                results = manual_search.search(artist=real_artist)
                print(f"   Found {len(results)} results")
                
                if results:
                    print("   Top result:")
                    result = results[0]
                    print(f"     Artist: '{result.get('artist', '')}'")
                    print(f"     Title: '{result.get('title', '')}'")
                    print(f"     Score: {result.get('combined_score', 0)}%")
                    print(f"     File: {result.get('filename', '')}")
                else:
                    print("   ❌ NO RESULTS for exact artist match!")
            else:
                print("   ❌ No valid artist found in database")
    except Exception as e:
        print(f"   ❌ Error in manual search: {e}")
    
    # Test 4: Test with a very simple, common search
    print("\n4. TESTING SIMPLE SEARCHES:")
    simple_tests = ["a", "the", "mix", "remix"]
    
    for query in simple_tests:
        try:
            results = manual_search.search(query=query)
            print(f"   Query '{query}': {len(results)} results")
            if results and len(results) > 100:
                print(f"     ⚠️  Too many results - this suggests over-matching")
        except Exception as e:
            print(f"   ❌ Error searching '{query}': {e}")

def test_playlist_entry():
    """Test a specific playlist entry to see what happens."""
    
    print("\n" + "=" * 50)
    print("🎵 TESTING SPECIFIC PLAYLIST ENTRY")
    print("=" * 50)
    
    # Test with a known problematic entry
    test_artist = "Endymion"
    test_title = "Abduction"
    
    print(f"Testing: '{test_artist} - {test_title}'")
    
    try:
        cache_manager = CacheManager()
        string_matcher = StringMatcher(threshold=75)
        manual_search = ManualSearch(cache_manager, string_matcher)
        
        # Test different search approaches
        print("\nApproach 1: General query")
        results1 = manual_search.search(query=f"{test_artist} {test_title}")
        print(f"  Results: {len(results1)}")
        
        print("\nApproach 2: Separate artist/title")
        results2 = manual_search.search(artist=test_artist, title=test_title)
        print(f"  Results: {len(results2)}")
        
        print("\nApproach 3: Artist only")
        results3 = manual_search.search(artist=test_artist)
        print(f"  Results: {len(results3)}")
        
        print("\nApproach 4: Title only")
        results4 = manual_search.search(title=test_title)
        print(f"  Results: {len(results4)}")
        
        # Show best results from each approach
        all_results = [
            ("General query", results1),
            ("Artist/Title", results2), 
            ("Artist only", results3),
            ("Title only", results4)
        ]
        
        print("\nBest results from each approach:")
        for approach_name, results in all_results:
            if results:
                best = results[0]
                print(f"  {approach_name}: {best.get('combined_score', 0)}% - {best.get('filename', '')}")
            else:
                print(f"  {approach_name}: No results")
                
    except Exception as e:
        print(f"❌ Error in playlist entry test: {e}")

def main():
    """Main debug function."""
    print("🔧 MUSIC INDEXER DEBUG SCRIPT")
    print("This will help us find what's wrong with your search")
    print()
    
    test_basic_search()
    test_playlist_entry()
    
    print("\n" + "=" * 50)
    print("💡 DIAGNOSIS COMPLETE")
    print("=" * 50)
    print("Please share the output above so we can identify the exact problem!")

if __name__ == "__main__":
    main()
