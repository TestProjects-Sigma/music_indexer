"""
Enhanced indexing workflow for electronic music collections.
This ensures the metadata fixes are permanently applied during indexing.
"""
import os
import time
import sqlite3

def enhanced_indexing_with_metadata_validation(music_indexer, directories=None, 
                                              extract_audio_metadata=True, 
                                              progress_callback=None,
                                              validate_existing=True):
    """
    Enhanced indexing that automatically validates and fixes metadata.
    
    Args:
        music_indexer: The music indexer instance
        directories (list): Directories to index
        extract_audio_metadata (bool): Whether to extract full audio metadata
        progress_callback (function): Progress callback
        validate_existing (bool): Whether to validate existing metadata
    
    Returns:
        dict: Indexing results with validation info
    """
    start_time = time.time()
    
    if directories is None:
        directories = music_indexer.config_manager.get_music_directories()
    
    if not directories:
        return {'success': False, 'message': 'No directories specified'}
    
    mode = "full metadata" if extract_audio_metadata else "fast mode"
    print(f"🎵 Starting enhanced indexing in {mode}")
    print(f"📂 Directories: {len(directories)}")
    
    # Phase 1: Scan directories for files (parallel)
    if progress_callback:
        progress_callback(0, "Scanning directories for audio files...")
    
    audio_files = music_indexer.file_scanner.scan_directories_parallel(
        directories, 
        callback=lambda count, msg: progress_callback(count, f"Scanning: {msg}") if progress_callback else None
    )
    
    if not audio_files:
        return {'success': False, 'message': 'No audio files found'}
    
    print(f"🔍 Found {len(audio_files)} audio files to process")
    
    # Phase 2: Check for existing files and validate metadata quality
    if progress_callback:
        progress_callback(len(audio_files), "Checking existing files and metadata quality...")
    
    existing_files = set()
    problematic_files = set()
    
    try:
        # Get existing files
        cached_files = music_indexer.cache_manager.get_all_files()
        
        for cached_file in cached_files:
            file_path = cached_file.get('file_path', '')
            existing_files.add(file_path)
            
            # Check if metadata needs fixing (electronic music validation)
            if validate_existing and _needs_metadata_fix(cached_file):
                problematic_files.add(file_path)
        
        print(f"📊 Found {len(existing_files)} already indexed files")
        if problematic_files:
            print(f"⚠️  Found {len(problematic_files)} files with problematic metadata")
    
    except Exception as e:
        print(f"⚠️  Could not load existing files: {str(e)}")
    
    # Phase 3: Determine which files to process
    # Include new files + problematic existing files
    files_to_process = []
    
    # Add new files
    new_files = [f for f in audio_files if f not in existing_files]
    files_to_process.extend(new_files)
    
    # Add problematic existing files (for re-processing)
    if validate_existing:
        problematic_existing = [f for f in problematic_files if f in audio_files]
        files_to_process.extend(problematic_existing)
    
    # Remove duplicates
    files_to_process = list(set(files_to_process))
    
    if not files_to_process:
        print("✅ All files are already indexed with good metadata")
        return {
            'success': True, 
            'message': f'All {len(audio_files)} files already have good metadata',
            'total_files': len(audio_files),
            'new_files': 0,
            'fixed_files': 0,
            'processing_time': time.time() - start_time
        }
    
    print(f"🔧 Processing {len(files_to_process)} files:")
    print(f"   • New files: {len(new_files)}")
    print(f"   • Files needing metadata fixes: {len(files_to_process) - len(new_files)}")
    
    # Phase 4: Extract metadata with enhanced electronic music parsing
    if progress_callback:
        progress_callback(0, f"Extracting metadata from {len(files_to_process)} files...")
    
    metadata_list = music_indexer.metadata_extractor.extract_metadata_parallel(
        files_to_process,
        extract_audio_metadata=extract_audio_metadata,
        callback=lambda count, msg: progress_callback(count, msg) if progress_callback else None
    )
    
    # Phase 5: Validate metadata quality before storing
    if progress_callback:
        progress_callback(len(metadata_list), "Validating and storing metadata...")
    
    stored_count = 0
    fixed_count = 0
    
    for metadata in metadata_list:
        if metadata:
            # Validate the metadata quality
            if _validate_metadata_quality(metadata):
                # Store in cache (this will update existing records)
                if music_indexer.cache_manager.cache_file_metadata(metadata):
                    stored_count += 1
                    
                    # Check if this was a fix
                    if metadata.get('file_path') in problematic_files:
                        fixed_count += 1
            else:
                print(f"⚠️  Poor metadata quality for: {metadata.get('filename', 'unknown')}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    result = {
        'success': True,
        'message': f'Enhanced indexing complete: {stored_count} files processed, {fixed_count} metadata fixes applied',
        'total_files': len(audio_files),
        'new_files': len(new_files),
        'fixed_files': fixed_count,
        'already_indexed': len(existing_files) - len(problematic_files),
        'processing_time': processing_time
    }
    
    print(f"✅ Enhanced indexing complete in {processing_time:.2f} seconds")
    print(f"📊 Results: {stored_count} processed, {fixed_count} metadata improved")
    
    return result


def _needs_metadata_fix(cached_file):
    """
    Check if a cached file needs metadata fixing.
    Detects electronic music metadata problems.
    
    Args:
        cached_file (dict): Cached file metadata
        
    Returns:
        bool: True if metadata needs fixing
    """
    artist = cached_file.get('artist', '').strip()
    title = cached_file.get('title', '').strip()
    filename = cached_file.get('filename', '')
    
    # Check for track number artists (critical issue)
    if artist and (artist.isdigit() or 
                   len(artist) <= 3 and artist.lower() in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                                                            'a1', 'a2', 'a3', 'b1', 'b2', 'b3', 'c1', 'c2']):
        return True
    
    # Check for underscore problems
    if artist and ('_' in artist or artist.endswith('_')):
        return True
    
    if title and (title.startswith('_') or '_' in title):
        return True
    
    # Check if filename suggests better parsing is possible
    if filename and ('_-_' in filename or filename.startswith(('01-', '02-', 'a1_', 'b2_'))):
        # Check if current parsing missed the pattern
        if not artist or len(artist) <= 3:
            return True
    
    return False


def _validate_metadata_quality(metadata):
    """
    Validate that metadata is of good quality for electronic music.
    
    Args:
        metadata (dict): Metadata to validate
        
    Returns:
        bool: True if metadata is good quality
    """
    artist = metadata.get('artist', '').strip()
    title = metadata.get('title', '').strip()
    
    # Basic validation
    if not artist or not title:
        return len(title) > 2  # At least need a good title
    
    # Check artist quality
    if artist.isdigit() or len(artist) <= 1:
        return False
    
    # Check for track number artists
    if artist.lower() in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                          'a1', 'a2', 'a3', 'b1', 'b2', 'b3']:
        return False
    
    # Check title quality
    if len(title) <= 1 or title.startswith('_'):
        return False
    
    return True


def integrate_enhanced_indexing(music_indexer):
    """
    Integrate enhanced indexing into the music indexer.
    This replaces the standard indexing with electronic music optimized version.
    
    Args:
        music_indexer: The music indexer instance
    """
    # Store original method
    music_indexer._original_index_files = music_indexer.index_files
    
    def enhanced_index_files(directories=None, extract_audio_metadata=True, progress_callback=None):
        """Enhanced indexing method that replaces the original."""
        return enhanced_indexing_with_metadata_validation(
            music_indexer, 
            directories=directories,
            extract_audio_metadata=extract_audio_metadata,
            progress_callback=progress_callback,
            validate_existing=True
        )
    
    # Replace the indexing method
    music_indexer.index_files = enhanced_index_files
    
    print("✅ Enhanced electronic music indexing integrated")


# Integration instructions for your main application
"""
INTEGRATION INSTRUCTIONS:

1. Add this to your music_indexer/__init__.py file, in the MusicIndexer.__init__ method:

    from .utils.enhanced_indexing import integrate_enhanced_indexing
    
    # At the end of __init__:
    integrate_enhanced_indexing(self)

2. Or alternatively, call it when starting your app in main.py:

    from music_indexer.utils.enhanced_indexing import integrate_enhanced_indexing
    
    # After creating music_indexer instance:
    integrate_enhanced_indexing(music_indexer)

This will ensure that every indexing operation automatically:
- Uses the improved electronic music metadata parsing
- Validates existing metadata and fixes problems
- Maintains high metadata quality
- Works seamlessly with your existing app
"""