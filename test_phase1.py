#!/usr/bin/env python3
"""
Test script to measure Phase 1 improvements.
Run this with a small playlist sample to test the improvements.

Usage: python test_phase1.py path/to/your/playlist.txt
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from music_indexer.core.cache_manager import CacheManager
from music_indexer.search.auto_search import AutoSearch
from music_indexer.utils.logger import get_logger

logger = get_logger(log_level="INFO")

def test_phase1_improvements(playlist_file_path, max_test_entries=20):
    """
    Test Phase 1 improvements on a playlist file.
    
    Args:
        playlist_file_path (str): Path to your playlist text file
        max_test_entries (int): Maximum entries to test (for quick testing)
    """
    print("=" * 80)
    print("TESTING PHASE 1 IMPROVEMENTS")
    print("=" * 80)
    
    # Initialize components
    cache_manager = CacheManager()
    auto_search = AutoSearch(cache_manager)
    
    # Check database
    cache_stats = cache_manager.get_cache_stats()
    print(f"Database contains {cache_stats['total_files']} indexed files")
    
    if cache_stats['total_files'] == 0:
        print("❌ ERROR: No files in database! Please index your music collection first.")
        return
    
    # Load test entries
    if not os.path.exists(playlist_file_path):
        print(f"❌ ERROR: Playlist file not found: {playlist_file_path}")
        return
    
    with open(playlist_file_path, 'r', encoding='utf-8') as f:
        all_entries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Limit for testing
    test_entries = all_entries[:max_test_entries]
    
    print(f"Testing with {len(test_entries)} entries (from {len(all_entries)} total)")
    print(f"Auto search threshold: {auto_search.string_matcher.threshold}")
    print()
    
    # Test each entry
    results = []
    found_count = 0
    high_confidence_count = 0
    
    for i, entry in enumerate(test_entries, 1):
        print(f"{i:2d}. Testing: '{entry}'")
        
        # Parse the entry
        parsed = auto_search._parse_match_line(entry)
        if not parsed:
            print("    ❌ Could not parse entry")
            continue
        
        # Generate variants to show what we're trying
        variants = auto_search.generate_search_variants(entry)
        print(f"    🔍 Search variants: {variants}")
        
        # Find matches
        matches = auto_search._find_matches_for_entry(parsed)
        
        if matches:
            found_count += 1
            best_match = matches[0]
            best_score = best_match.get('combined_score', 0)
            
            if best_score >= 80:
                high_confidence_count += 1
                status = "✅ HIGH CONFIDENCE"
            elif best_score >= 70:
                status = "✓ GOOD"
            else:
                status = "⚠ LOW CONFIDENCE"
            
            print(f"    {status} - Found {len(matches)} matches")
            print(f"    📁 Best: {best_match.get('filename', 'unknown')}")
            print(f"    🎵 Artist: '{best_match.get('artist', '')}', Title: '{best_match.get('title', '')}'")
            print(f"    📊 Score: {best_score:.1f}% (A:{best_match.get('artist_score', 0):.0f}, "
                  f"T:{best_match.get('title_score', 0):.0f}, F:{best_match.get('filename_score', 0):.0f})")
            
            results.append({
                'entry': entry,
                'found': True,
                'score': best_score,
                'filename': best_match.get('filename', 'unknown')
            })
        else:
            print("    ❌ NO MATCHES FOUND")
            results.append({
                'entry': entry,
                'found': False,
                'score': 0,
                'filename': None
            })
        
        print()
    
    # Summary statistics
    total_entries = len(test_entries)
    success_rate = (found_count / total_entries) * 100 if total_entries > 0 else 0
    high_confidence_rate = (high_confidence_count / total_entries) * 100 if total_entries > 0 else 0
    
    print("=" * 80)
    print("PHASE 1 TEST RESULTS")
    print("=" * 80)
    print(f"Total entries tested: {total_entries}")
    print(f"Found matches: {found_count} ({success_rate:.1f}%)")
    print(f"High confidence (80%+): {high_confidence_count} ({high_confidence_rate:.1f}%)")
    print(f"Good matches (70%+): {sum(1 for r in results if r['found'] and r['score'] >= 70)} matches")
    
    # Show failed matches for analysis
    failed = [r for r in results if not r['found']]
    if failed:
        print(f"\n❌ FAILED MATCHES ({len(failed)} entries):")
        for result in failed[:10]:  # Show first 10 failed
            print(f"  • '{result['entry']}'")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if success_rate >= 85:
        print("  🎉 Excellent results! Phase 1 improvements are working well.")
        print("  🚀 Consider running on your full playlist now.")
    elif success_rate >= 70:
        print("  👍 Good improvement! Consider trying Phase 2 enhancements.")
        print("  🔧 You might also try lowering the similarity threshold to 60-65.")
    elif success_rate >= 50:
        print("  📈 Some improvement, but more work needed.")
        print("  🔧 Try lowering similarity threshold and implementing Phase 2.")
    else:
        print("  ⚠️  Low success rate. Check that your music files have good metadata.")
        print("  🔍 Try manual search on some failed entries to see if they work there.")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"  1. If results look good, replace your auto_search.py with the improved version")
    print(f"  2. Test with your full playlist")
    print(f"  3. If you need better results, implement Phase 2 multi-pass search")
    
    return {
        'total': total_entries,
        'found': found_count,
        'success_rate': success_rate,
        'high_confidence_rate': high_confidence_rate
    }

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_phase1.py <playlist_file> [max_entries]")
        print("Example: python test_phase1.py my_playlist.txt 50")
        print("\nThis will test Phase 1 improvements on your playlist file.")
        return 1
    
    playlist_file = sys.argv[1]
    max_entries = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    test_phase1_improvements(playlist_file, max_entries)
    return 0

if __name__ == "__main__":
    sys.exit(main())