#!/usr/bin/env python3
"""
Quick script to fix your existing database with proper metadata parsing.
Run this after updating your metadata_extractor.py
"""
import sqlite3
import os
import re
import sys

def fix_database_metadata(db_path="cache/music_cache.db"):
    """
    Fix the problematic metadata in your existing database.
    This will correct all the track number and underscore issues.
    """
    
    print("🎵 Electronic Music Database Fix Script")
    print("=" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please check the path and try again.")
        return False
    
    # Electronic music labels from your collection
    known_labels = {'dps', 'trt', 'pms', 'sq', 'doc', 'vmc', 'dwm', 'apc', 'rfl', 'mim'}
    
    def parse_filename_fixed(filename):
        """Fixed filename parser for electronic music."""
        # Remove file extension
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # CRITICAL FIX 1: Remove track numbers and vinyl positions FIRST
        track_patterns = [
            r'^[a-z]?\d+[-_]\s*',  # a1-, 01-, 101-, a1_, etc.
            r'^\d+\s*[-_]\s*',     # Just numbers: 01-, 02-
        ]
        
        for pattern in track_patterns:
            base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
        
        # CRITICAL FIX 2: Handle the _-_ pattern (74% of your files)
        underscore_dash_pattern = r'^(.+?)_-_(.+?)(?:-([a-z]{2,4}))?$'
        underscore_dash_match = re.match(underscore_dash_pattern, base_name, re.IGNORECASE)
        if underscore_dash_match:
            raw_artist = underscore_dash_match.group(1)
            raw_title = underscore_dash_match.group(2)
            
            # Clean up the artist (remove trailing underscores)
            artist = re.sub(r'_+$', '', raw_artist).replace('_', ' ').strip()
            
            # Clean up the title (remove leading underscores)
            title = re.sub(r'^_+', '', raw_title).replace('_', ' ').strip()
            
            return artist, title
        
        # CRITICAL FIX 3: Handle standard dash separation
        dash_parts = base_name.split('-')
        if len(dash_parts) >= 2:
            artist = dash_parts[0].replace('_', ' ').strip()
            
            # Handle label at the end
            if len(dash_parts) > 2 and dash_parts[-1].lower() in known_labels:
                title = '-'.join(dash_parts[1:-1]).replace('_', ' ').strip()
            else:
                title = '-'.join(dash_parts[1:]).replace('_', ' ').strip()
            
            return artist, title
        
        # CRITICAL FIX 4: Handle underscore separation (without _-_)
        if '_' in base_name and '_-_' not in base_name:
            parts = base_name.split('_', 1)  # Split only on first underscore
            artist = parts[0].strip()
            title = parts[1].replace('_', ' ').strip() if len(parts) > 1 else ''
            
            return artist, title
        
        # Fallback - treat as title only
        return None, base_name.replace('_', ' ').strip()
    
    try:
        # Connect to database
        print(f"📂 Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total count first
        cursor.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]
        print(f"📊 Total files in database: {total_files:,}")
        
        # Find problematic files (simplified query for compatibility)
        print("🔍 Finding files with problematic metadata...")
        cursor.execute("""
            SELECT file_path, filename, artist, title 
            FROM files 
            WHERE 
                (artist LIKE '0%' OR artist LIKE '1%' OR artist LIKE '2%' OR 
                 artist LIKE 'a0%' OR artist LIKE 'a1%' OR artist LIKE 'a2%' OR
                 artist LIKE 'b0%' OR artist LIKE 'b1%' OR artist LIKE 'b2%' OR
                 artist LIKE '%_%')
                OR (title LIKE '%_%')
            ORDER BY file_path
        """)
        
        problematic_files = cursor.fetchall()
        print(f"🚨 Found {len(problematic_files):,} files with problematic metadata ({len(problematic_files)/total_files*100:.1f}%)")
        
        if len(problematic_files) == 0:
            print("✅ No problematic files found! Your database looks good.")
            conn.close()
            return True
        
        # Show some examples
        print("\n📋 Examples of problematic files:")
        for i, (file_path, filename, old_artist, old_title) in enumerate(problematic_files[:5]):
            print(f"  {i+1}. {filename}")
            print(f"     Current: Artist='{old_artist}', Title='{old_title}'")
            
            # Show what the fix would be
            new_artist, new_title = parse_filename_fixed(filename)
            print(f"     Fixed:   Artist='{new_artist or '(empty)'}', Title='{new_title or '(empty)'}'")
            print()
        
        # Ask for confirmation
        response = input(f"🤔 Fix {len(problematic_files):,} problematic files? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled by user")
            conn.close()
            return False
        
        # Process the fixes
        print(f"🔧 Processing {len(problematic_files):,} files...")
        fixed_count = 0
        
        for i, (file_path, filename, old_artist, old_title) in enumerate(problematic_files):
            # Show progress every 1000 files
            if i % 1000 == 0 and i > 0:
                print(f"   Progress: {i:,}/{len(problematic_files):,} ({i/len(problematic_files)*100:.1f}%)")
            
            # Re-parse filename using fixed parser
            new_artist, new_title = parse_filename_fixed(filename)
            
            # Check if we actually improved something
            improved = False
            
            # Check if artist improved
            old_artist_bad = (not old_artist or 
                            old_artist.isdigit() or 
                            len(old_artist) <= 2 or
                            old_artist.endswith('_'))
            
            new_artist_good = (new_artist and 
                             len(new_artist) > 1 and 
                             not new_artist.isdigit() and
                             not new_artist.endswith('_'))
            
            if old_artist_bad and new_artist_good:
                improved = True
            
            # Check if title improved
            old_title_bad = (not old_title or 
                           old_title.startswith('_') or 
                           old_title.endswith('_') or
                           '_' in old_title)
            
            new_title_good = (new_title and 
                            len(new_title) > 1 and
                            not new_title.startswith('_'))
            
            if old_title_bad and new_title_good:
                improved = True
            
            # Update if improved
            if improved:
                cursor.execute("""
                    UPDATE files 
                    SET artist = ?, title = ?, artist_from_filename = ?, title_from_filename = ?
                    WHERE file_path = ?
                """, (
                    new_artist or old_artist,
                    new_title or old_title,
                    bool(new_artist),
                    bool(new_title),
                    file_path
                ))
                
                fixed_count += 1
                
                # Show first few fixes
                if fixed_count <= 10:
                    print(f"✅ FIXED: {filename}")
                    print(f"   Old: '{old_artist}' - '{old_title}'")
                    print(f"   New: '{new_artist or old_artist}' - '{new_title or old_title}'")
        
        # Commit all changes
        print("💾 Committing changes to database...")
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 DATABASE FIX COMPLETE!")
        print(f"✅ Fixed metadata for {fixed_count:,} files")
        print(f"📊 Improvement rate: {fixed_count/len(problematic_files)*100:.1f}%")
        print("\n🚀 Your playlist matching should work MUCH better now!")
        print("\nNext steps:")
        print("1. Update your metadata_extractor.py with the fixed version")
        print("2. Update your string_matcher.py with the electronic music version")
        print("3. Try your playlist matching again!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database fix: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def analyze_improvements(db_path="cache/music_cache.db"):
    """
    Analyze the improvements made to the database.
    """
    
    print("\n🔍 ANALYZING DATABASE IMPROVEMENTS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for remaining problematic files
        cursor.execute("""
            SELECT COUNT(*) 
            FROM files 
            WHERE artist LIKE '0%' OR artist LIKE '1%' OR artist LIKE '2%' OR 
                  artist LIKE 'a0%' OR artist LIKE 'a1%' OR artist LIKE 'a2%'
        """)
        remaining_bad_artists = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM files 
            WHERE title LIKE '%_%' OR title LIKE '_%' OR title LIKE '%_'
        """)
        remaining_bad_titles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]
        
        print(f"📊 Database Analysis:")
        print(f"   Total files: {total_files:,}")
        print(f"   Files with numeric artists: {remaining_bad_artists:,} ({remaining_bad_artists/total_files*100:.1f}%)")
        print(f"   Files with underscore titles: {remaining_bad_titles:,} ({remaining_bad_titles/total_files*100:.1f}%)")
        
        # Show some examples of good metadata now
        cursor.execute("""
            SELECT filename, artist, title 
            FROM files 
            WHERE artist IS NOT NULL 
              AND title IS NOT NULL 
              AND artist != '' 
              AND title != ''
              AND NOT (artist LIKE '0%' OR artist LIKE '1%' OR artist LIKE '2%')
              AND LENGTH(artist) > 2
              AND LENGTH(title) > 2
            ORDER BY RANDOM() 
            LIMIT 10
        """)
        
        good_examples = cursor.fetchall()
        
        print(f"\n✅ Examples of good metadata ({len(good_examples)} shown):")
        for filename, artist, title in good_examples:
            print(f"   {artist} - {title}")
            print(f"     ({filename})")
        
        conn.close()
        
        # Calculate improvement
        total_problems = remaining_bad_artists + remaining_bad_titles
        if total_problems < total_files * 0.1:  # Less than 10% problematic
            print(f"\n🎉 EXCELLENT! Your database now has high-quality metadata!")
            print(f"   Only {total_problems:,} files still have minor issues ({total_problems/total_files*100:.1f}%)")
        else:
            print(f"\n⚠️  Some issues remain: {total_problems:,} files ({total_problems/total_files*100:.1f}%)")
            print(f"   You may want to run the fix script again or investigate manually.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")


if __name__ == "__main__":
    print("🎵 Electronic Music Database Fix Tool")
    print("=" * 50)
    print("This script will fix the track number and underscore issues")
    print("identified in your electronic music collection analysis.")
    print()
    
    # Check command line arguments
    db_path = "cache/music_cache.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"Database path: {db_path}")
    print()
    
    # Run the fix
    success = fix_database_metadata(db_path)
    
    if success:
        # Analyze improvements
        analyze_improvements(db_path)
        
        print("\n" + "=" * 50)
        print("🎯 SUMMARY:")
        print("Your electronic music collection should now have much better")
        print("metadata parsing, which will dramatically improve playlist matching!")
        print()
        print("The main fixes applied:")
        print("✅ Removed track numbers from artist names (01, 02, a1, b2, etc.)")
        print("✅ Fixed underscore hell in artist/title names")
        print("✅ Proper handling of _-_ patterns (74% of your files)")
        print("✅ Recognition of electronic music labels (-dps, -trt, etc.)")
        print()
        print("🚀 Try your playlist matching again - it should work much better!")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")
        sys.exit(1)