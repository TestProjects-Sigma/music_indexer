#!/usr/bin/env python3
"""
Database analysis script to understand your music collection patterns.
This will help create the perfect matching solution for your files.

Usage: python analyze_database.py
(Make sure your database is at cache/music_cache.db or update the path)
"""
import sqlite3
import os
import re
from collections import Counter

def analyze_database(db_path="cache/music_cache.db"):
    """
    Analyze the music database and export results to text files.
    """
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("Please update the db_path in the script or copy your database to this location.")
        return
    
    print(f"🔍 Analyzing database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create output directory
        output_dir = "database_analysis"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📁 Results will be saved to: {output_dir}/")
        
        # Run all analyses
        analyze_basic_info(cursor, output_dir)
        analyze_filename_patterns(cursor, output_dir)
        analyze_problematic_cases(cursor, output_dir)
        analyze_metadata_coverage(cursor, output_dir)
        analyze_music_styles(cursor, output_dir)
        analyze_good_examples(cursor, output_dir)
        
        conn.close()
        
        print("✅ Analysis complete! Check the files in database_analysis/ folder")
        print("\n📧 Please share the contents of these files so I can create the perfect solution:")
        print("   - basic_info.txt")
        print("   - filename_patterns.txt") 
        print("   - problematic_cases.txt")
        print("   - metadata_coverage.txt")
        
    except Exception as e:
        print(f"❌ Error analyzing database: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_basic_info(cursor, output_dir):
    """Get basic database information."""
    print("📊 Analyzing basic info...")
    
    with open(f"{output_dir}/basic_info.txt", "w", encoding="utf-8") as f:
        f.write("=== BASIC DATABASE INFO ===\n\n")
        
        # Total files
        cursor.execute("SELECT COUNT(*) FROM files")
        total = cursor.fetchone()[0]
        f.write(f"Total files: {total:,}\n\n")
        
        # Format distribution
        f.write("Format distribution:\n")
        cursor.execute("SELECT format, COUNT(*) as count FROM files GROUP BY format ORDER BY count DESC")
        for format_type, count in cursor.fetchall():
            percentage = (count / total) * 100
            f.write(f"  {format_type}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        # Files with/without metadata
        cursor.execute("SELECT COUNT(*) FROM files WHERE artist IS NOT NULL AND artist != ''")
        with_artist = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM files WHERE title IS NOT NULL AND title != ''")
        with_title = cursor.fetchone()[0]
        
        f.write(f"Files with artist metadata: {with_artist:,} ({(with_artist/total)*100:.1f}%)\n")
        f.write(f"Files with title metadata: {with_title:,} ({(with_title/total)*100:.1f}%)\n")

def analyze_filename_patterns(cursor, output_dir):
    """Analyze filename patterns to understand naming conventions."""
    print("📋 Analyzing filename patterns...")
    
    with open(f"{output_dir}/filename_patterns.txt", "w", encoding="utf-8") as f:
        f.write("=== FILENAME PATTERNS ANALYSIS ===\n\n")
        
        # Get all filenames for pattern analysis
        cursor.execute("SELECT filename FROM files LIMIT 5000")  # Sample first 5000
        filenames = [row[0] for row in cursor.fetchall()]
        
        # Pattern categories
        patterns = {
            'track_number_dash': 0,      # 01-, 02-, etc.
            'track_number_underscore': 0, # 01_, 02_, etc.
            'underscore_dash': 0,        # _-_
            'multiple_underscores': 0,   # ___
            'multiple_dashes': 0,        # ---
            'parentheses': 0,            # ()
            'brackets': 0,               # []
            'has_remix': 0,              # remix/mix
            'has_feat': 0,               # feat/ft
            'starts_with_letter_number': 0, # a01, b02, etc.
        }
        
        pattern_examples = {key: [] for key in patterns.keys()}
        
        for filename in filenames:
            if re.match(r'^\d{1,3}-', filename):
                patterns['track_number_dash'] += 1
                if len(pattern_examples['track_number_dash']) < 10:
                    pattern_examples['track_number_dash'].append(filename)
            
            if re.match(r'^\d{1,3}_', filename):
                patterns['track_number_underscore'] += 1
                if len(pattern_examples['track_number_underscore']) < 10:
                    pattern_examples['track_number_underscore'].append(filename)
            
            if '_-_' in filename:
                patterns['underscore_dash'] += 1
                if len(pattern_examples['underscore_dash']) < 10:
                    pattern_examples['underscore_dash'].append(filename)
            
            if filename.count('_') >= 3:
                patterns['multiple_underscores'] += 1
                if len(pattern_examples['multiple_underscores']) < 10:
                    pattern_examples['multiple_underscores'].append(filename)
            
            if filename.count('-') >= 3:
                patterns['multiple_dashes'] += 1
                if len(pattern_examples['multiple_dashes']) < 10:
                    pattern_examples['multiple_dashes'].append(filename)
            
            if '(' in filename:
                patterns['parentheses'] += 1
                if len(pattern_examples['parentheses']) < 10:
                    pattern_examples['parentheses'].append(filename)
            
            if re.search(r'(remix|mix)', filename.lower()):
                patterns['has_remix'] += 1
                if len(pattern_examples['has_remix']) < 10:
                    pattern_examples['has_remix'].append(filename)
            
            if re.search(r'(feat|ft\.)', filename.lower()):
                patterns['has_feat'] += 1
                if len(pattern_examples['has_feat']) < 10:
                    pattern_examples['has_feat'].append(filename)
            
            if re.match(r'^[a-z]\d+', filename.lower()):
                patterns['starts_with_letter_number'] += 1
                if len(pattern_examples['starts_with_letter_number']) < 10:
                    pattern_examples['starts_with_letter_number'].append(filename)
        
        # Write patterns with examples
        total_analyzed = len(filenames)
        f.write(f"Analyzed {total_analyzed:,} filenames:\n\n")
        
        for pattern_name, count in patterns.items():
            if count > 0:
                percentage = (count / total_analyzed) * 100
                f.write(f"{pattern_name}: {count:,} files ({percentage:.1f}%)\n")
                
                if pattern_examples[pattern_name]:
                    f.write("  Examples:\n")
                    for example in pattern_examples[pattern_name][:5]:
                        f.write(f"    {example}\n")
                f.write("\n")

def analyze_problematic_cases(cursor, output_dir):
    """Find cases that are likely causing matching problems."""
    print("⚠️  Analyzing problematic cases...")
    
    with open(f"{output_dir}/problematic_cases.txt", "w", encoding="utf-8") as f:
        f.write("=== PROBLEMATIC CASES ===\n\n")
        
        # Case 1: Files where artist is just a number (your main issue)
        f.write("1. Files with numeric artists (track number parsing issue):\n")
        cursor.execute("""
            SELECT filename, artist, title 
            FROM files 
            WHERE artist GLOB '[0-9]' OR artist GLOB '[0-9][0-9]' OR artist GLOB '[0-9][0-9][0-9]'
            LIMIT 20
        """)
        
        numeric_artists = cursor.fetchall()
        if not numeric_artists:
            # Try a broader search for likely numeric artists
            cursor.execute("""
                SELECT filename, artist, title 
                FROM files 
                WHERE artist LIKE '1' OR artist LIKE '01' OR artist LIKE '001'
                   OR artist LIKE '2' OR artist LIKE '02' OR artist LIKE '002'  
                   OR artist LIKE '3' OR artist LIKE '03' OR artist LIKE '003'
                   OR artist IN ('1','2','3','4','5','6','7','8','9','01','02','03','04','05','06','07','08','09','10','11','12')
                LIMIT 20
            """)
            numeric_artists = cursor.fetchall()
        
        for filename, artist, title in numeric_artists:
            f.write(f"   File: {filename}\n")
            f.write(f"   Artist: '{artist}' (should not be just a number!)\n")
            f.write(f"   Title: '{title}'\n\n")
        
        # Case 2: Files with very short artists/titles
        f.write("2. Files with very short metadata (likely parsing errors):\n")
        cursor.execute("""
            SELECT filename, artist, title 
            FROM files 
            WHERE (LENGTH(artist) <= 2 AND artist != '' AND artist IS NOT NULL) 
               OR (LENGTH(title) <= 2 AND title != '' AND title IS NOT NULL)
            LIMIT 15
        """)
        
        for filename, artist, title in cursor.fetchall():
            f.write(f"   File: {filename}\n")
            f.write(f"   Artist: '{artist}' Title: '{title}'\n\n")
        
        # Case 3: Files with underscores in metadata
        f.write("3. Files with underscores in artist/title (not cleaned properly):\n")
        cursor.execute("""
            SELECT filename, artist, title 
            FROM files 
            WHERE artist LIKE '%_%' OR title LIKE '%_%'
            LIMIT 15
        """)
        
        for filename, artist, title in cursor.fetchall():
            f.write(f"   File: {filename}\n")
            f.write(f"   Artist: '{artist}' Title: '{title}'\n\n")
        
        # Case 4: Files starting with numbers (track number prefix issue)
        f.write("4. Files with track number prefixes in filename:\n")
        cursor.execute("""
            SELECT filename, artist, title 
            FROM files 
            WHERE filename LIKE '0%-%' OR filename LIKE '1%-%' OR filename LIKE '2%-%'
               OR filename LIKE '0%_%' OR filename LIKE '1%_%' OR filename LIKE '2%_%'
            LIMIT 20
        """)
        
        for filename, artist, title in cursor.fetchall():
            f.write(f"   File: {filename}\n")
            f.write(f"   Artist: '{artist}' Title: '{title}'\n\n")

def analyze_metadata_coverage(cursor, output_dir):
    """Analyze metadata coverage and quality."""
    print("📈 Analyzing metadata coverage...")
    
    with open(f"{output_dir}/metadata_coverage.txt", "w", encoding="utf-8") as f:
        f.write("=== METADATA COVERAGE ANALYSIS ===\n\n")
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM files")
        total = cursor.fetchone()[0]
        
        # Files with complete metadata
        cursor.execute("""
            SELECT COUNT(*) FROM files 
            WHERE artist IS NOT NULL AND artist != '' 
              AND title IS NOT NULL AND title != ''
              AND LENGTH(artist) > 2 AND LENGTH(title) > 2
        """)
        complete = cursor.fetchone()[0]
        
        # Files with no metadata (will need filename parsing)
        cursor.execute("""
            SELECT COUNT(*) FROM files 
            WHERE (artist IS NULL OR artist = '' OR LENGTH(artist) <= 2)
              AND (title IS NULL OR title = '' OR LENGTH(title) <= 2)
        """)
        no_metadata = cursor.fetchone()[0]
        
        f.write(f"Complete metadata: {complete:,} ({(complete/total)*100:.1f}%)\n")
        f.write(f"No useful metadata: {no_metadata:,} ({(no_metadata/total)*100:.1f}%)\n")
        f.write(f"Partial metadata: {total-complete-no_metadata:,} ({((total-complete-no_metadata)/total)*100:.1f}%)\n\n")
        
        # Sample files with no metadata (these need filename parsing)
        f.write("Sample files that need filename parsing:\n")
        cursor.execute("""
            SELECT filename 
            FROM files 
            WHERE (artist IS NULL OR artist = '' OR LENGTH(artist) <= 2)
              AND (title IS NULL OR title = '' OR LENGTH(title) <= 2)
            LIMIT 10
        """)
        
        for (filename,) in cursor.fetchall():
            f.write(f"   {filename}\n")

def analyze_music_styles(cursor, output_dir):
    """Analyze what types of music are in the collection."""
    print("🎵 Analyzing music styles...")
    
    with open(f"{output_dir}/music_styles.txt", "w", encoding="utf-8") as f:
        f.write("=== MUSIC STYLES ANALYSIS ===\n\n")
        
        # Keywords in filenames that indicate music style
        keywords = [
            'remix', 'mix', 'edit', 'version', 'original', 'radio', 'club', 'vocal',
            'instrumental', 'extended', 'dub', 'house', 'techno', 'trance', 'dance',
            'electronic', 'edm', 'hardcore', 'hardstyle', 'drum', 'bass', 'dubstep'
        ]
        
        keyword_counts = {}
        
        for keyword in keywords:
            cursor.execute(f"""
                SELECT COUNT(*) FROM files 
                WHERE filename LIKE '%{keyword}%' 
                   OR artist LIKE '%{keyword}%' 
                   OR title LIKE '%{keyword}%'
            """)
            count = cursor.fetchone()[0]
            if count > 0:
                keyword_counts[keyword] = count
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        
        f.write("Music style keywords found:\n")
        cursor.execute("SELECT COUNT(*) FROM files")
        total = cursor.fetchone()[0]
        
        for keyword, count in sorted_keywords:
            percentage = (count / total) * 100
            f.write(f"   {keyword}: {count:,} files ({percentage:.1f}%)\n")

def analyze_good_examples(cursor, output_dir):
    """Find examples of files with good metadata for comparison."""
    print("✅ Finding good examples...")
    
    with open(f"{output_dir}/good_examples.txt", "w", encoding="utf-8") as f:
        f.write("=== GOOD EXAMPLES (files with clean metadata) ===\n\n")
        
        # Files with good metadata (avoiding numeric artists)
        cursor.execute("""
            SELECT filename, artist, title, format
            FROM files 
            WHERE artist IS NOT NULL AND title IS NOT NULL 
              AND LENGTH(artist) > 3 AND LENGTH(title) > 3
              AND artist NOT IN ('1','2','3','4','5','6','7','8','9','01','02','03','04','05','06','07','08','09','10','11','12')
              AND artist NOT LIKE '%_%'
              AND title NOT LIKE '%_%'
            LIMIT 20
        """)
        
        f.write("Files with clean, well-parsed metadata:\n")
        for filename, artist, title, format_type in cursor.fetchall():
            f.write(f"   File: {filename}\n")
            f.write(f"   Artist: '{artist}' | Title: '{title}' | Format: {format_type}\n\n")

def main():
    """Main function."""
    print("🎯 Music Database Analyzer")
    print("=" * 50)
    
    # Try common database locations
    possible_paths = [
        "cache/music_cache.db",
        "music_cache.db", 
        "../cache/music_cache.db",
        "music_indexer_cache.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Could not find database file!")
        print("Please:")
        print("1. Extract your music_cache.db from the zip file")
        print("2. Place it in one of these locations:")
        for path in possible_paths:
            print(f"   - {path}")
        print("3. Or edit this script to point to the correct location")
        return
    
    analyze_database(db_path)

if __name__ == "__main__":
    main()