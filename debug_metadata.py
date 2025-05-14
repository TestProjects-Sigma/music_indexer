#!/usr/bin/env python3
"""
Debug script to test metadata extraction and caching.
"""
import os
import sys
import time
import sqlite3

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from music_indexer.core.metadata_extractor import MetadataExtractor
from music_indexer.core.cache_manager import CacheManager
from music_indexer.utils.logger import get_logger

# Configure logging
logger = get_logger(log_level="DEBUG")

def test_extraction_and_caching(file_path):
    """Test metadata extraction and caching for a single file."""
    print(f"\nTesting file: {file_path}")
    print("-" * 50)
    
    # Create extractors and cache manager
    extractor = MetadataExtractor()
    cache_manager = CacheManager("cache/test_debug.db")
    
    # Step 1: Extract metadata
    print("Step 1: Extracting metadata...")
    start_time = time.time()
    metadata = extractor.extract_metadata(file_path)
    extract_time = time.time() - start_time
    
    if metadata:
        print(f"Extraction successful ({extract_time:.2f} seconds)")
        print("Metadata summary:")
        print(f"  Filename: {metadata.get('filename', 'Unknown')}")
        print(f"  Artist: {metadata.get('artist', 'Unknown')}")
        print(f"  Title: {metadata.get('title', 'Unknown')}")
        print(f"  Format: {metadata.get('format', 'Unknown')}")
        print(f"  Duration: {metadata.get('duration', 0):.2f} seconds")
        print(f"  Bitrate: {metadata.get('bitrate', 0)} kbps")
    else:
        print("Extraction failed!")
        return False
    
    # Step 2: Cache metadata
    print("\nStep 2: Caching metadata...")
    start_time = time.time()
    
    # Enable detailed SQLite logging
    def sqlite_trace_callback(statement):
        print(f"SQLite executing: {statement}")
    
    # Connect directly to the database for testing
    try:
        conn = sqlite3.connect(cache_manager.cache_file, timeout=30.0)
        conn.set_trace_callback(sqlite_trace_callback)
        conn.close()
    except Exception as e:
        print(f"Error setting up SQLite tracing: {e}")
    
    # Try caching the metadata
    success = cache_manager.cache_file_metadata(metadata)
    cache_time = time.time() - start_time
    
    if success:
        print(f"Caching successful ({cache_time:.2f} seconds)")
    else:
        print("Caching failed!")
    
    return success

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python debug_metadata.py <path_to_audio_file>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return 1
    
    if test_extraction_and_caching(file_path):
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())