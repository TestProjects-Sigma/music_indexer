#!/usr/bin/env python3
"""
Cleanup script for Music Indexer project.
Removes temporary files, caches, and logs before committing to GitHub.
"""
import os
import shutil
import glob
import argparse
import sys

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Clean up temporary files in the Music Indexer project")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--keep-config", action="store_true", help="Keep config.ini file")
    parser.add_argument("--keep-logs", action="store_true", help="Keep log files")
    parser.add_argument("--keep-cache", action="store_true", help="Keep cache files and database")
    return parser.parse_args()

def get_project_root():
    """Get the project root directory."""
    # Assuming this script is in the project root or a direct subdirectory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're in the project root
    if os.path.exists(os.path.join(script_dir, "music_indexer")):
        return script_dir
    
    # Check if the parent directory is the project root
    parent_dir = os.path.dirname(script_dir)
    if os.path.exists(os.path.join(parent_dir, "music_indexer")):
        return parent_dir
    
    print("Error: Could not determine project root directory.")
    sys.exit(1)

def cleanup_pycache(root_dir, dry_run=False):
    """Remove all __pycache__ directories and .pyc files."""
    print("\nCleaning up Python cache files...")
    
    # Find .pyc and .pyo files first (before removing directories)
    pyc_files = []
    for ext in ["*.pyc", "*.pyo", "*.pyd"]:
        pattern = os.path.join(root_dir, "**", ext)
        pyc_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove individual files first
    removed_files = 0
    for pyc_file in pyc_files:
        if os.path.exists(pyc_file):  # Check if file still exists
            if dry_run:
                print(f"Would remove file: {pyc_file}")
                removed_files += 1
            else:
                try:
                    print(f"Removing file: {pyc_file}")
                    os.remove(pyc_file)
                    removed_files += 1
                except (FileNotFoundError, PermissionError) as e:
                    print(f"Could not remove {pyc_file}: {e}")
    
    # Find and remove __pycache__ directories
    pycache_dirs = []
    for root, dirs, _ in os.walk(root_dir):
        for dir in dirs:
            if dir == "__pycache__":
                pycache_dirs.append(os.path.join(root, dir))
    
    # Remove directories after files
    removed_dirs = 0
    for pycache_dir in pycache_dirs:
        if os.path.exists(pycache_dir):  # Check if directory still exists
            if dry_run:
                print(f"Would remove directory: {pycache_dir}")
                removed_dirs += 1
            else:
                try:
                    print(f"Removing directory: {pycache_dir}")
                    shutil.rmtree(pycache_dir)
                    removed_dirs += 1
                except (FileNotFoundError, PermissionError) as e:
                    print(f"Could not remove {pycache_dir}: {e}")
    
    print(f"Found {len(pycache_dirs)} __pycache__ directories and {len(pyc_files)} .pyc/.pyo files")
    print(f"Removed {removed_dirs} directories and {removed_files} files")

def cleanup_cache(root_dir, dry_run=False):
    """Remove cache directory and database files."""
    print("\nCleaning up cache files and databases...")
    
    # Find and remove cache directory
    cache_dir = os.path.join(root_dir, "cache")
    if os.path.exists(cache_dir):
        if dry_run:
            print(f"Would remove directory: {cache_dir}")
        else:
            print(f"Removing directory: {cache_dir}")
            shutil.rmtree(cache_dir)
    
    # Find and remove database files
    db_files = []
    for ext in ["*.db", "*.sqlite", "*.sqlite3"]:
        pattern = os.path.join(root_dir, "**", ext)
        db_files.extend(glob.glob(pattern, recursive=True))
    
    # Report and delete
    for db_file in db_files:
        if dry_run:
            print(f"Would remove file: {db_file}")
        else:
            print(f"Removing file: {db_file}")
            os.remove(db_file)
    
    print(f"Found {1 if os.path.exists(cache_dir) else 0} cache directories and {len(db_files)} database files")

def cleanup_logs(root_dir, dry_run=False):
    """Remove log files and directories."""
    print("\nCleaning up log files...")
    
    # Find and remove logs directory
    logs_dir = os.path.join(root_dir, "logs")
    if os.path.exists(logs_dir):
        if dry_run:
            print(f"Would remove directory: {logs_dir}")
        else:
            print(f"Removing directory: {logs_dir}")
            shutil.rmtree(logs_dir)
    
    # Find and remove individual log files
    log_files = []
    for ext in ["*.log", "*.log.*"]:
        pattern = os.path.join(root_dir, "**", ext)
        log_files.extend(glob.glob(pattern, recursive=True))
    
    # Report and delete
    for log_file in log_files:
        if dry_run:
            print(f"Would remove file: {log_file}")
        else:
            print(f"Removing file: {log_file}")
            os.remove(log_file)
    
    print(f"Found {1 if os.path.exists(logs_dir) else 0} log directories and {len(log_files)} log files")

def cleanup_config(root_dir, dry_run=False):
    """Remove configuration files."""
    print("\nCleaning up configuration files...")
    
    # Find and remove config.ini
    config_file = os.path.join(root_dir, "config.ini")
    if os.path.exists(config_file):
        if dry_run:
            print(f"Would remove file: {config_file}")
        else:
            print(f"Removing file: {config_file}")
            os.remove(config_file)
        print("Found 1 config file")
    else:
        print("No config files found")

def cleanup_temp_files(root_dir, dry_run=False):
    """Remove temporary files."""
    print("\nCleaning up temporary files...")
    
    # Patterns for temporary files
    temp_patterns = [
        "*.tmp", "*.bak", "*.swp", "*.~*", 
        "*.DS_Store", "Thumbs.db", "desktop.ini",
        "*.pytest_cache", ".coverage"
    ]
    
    # Find temporary files
    temp_files = []
    for pattern in temp_patterns:
        glob_pattern = os.path.join(root_dir, "**", pattern)
        temp_files.extend(glob.glob(glob_pattern, recursive=True))
    
    # Report and delete
    for temp_file in temp_files:
        if dry_run:
            print(f"Would remove file: {temp_file}")
        else:
            print(f"Removing file: {temp_file}")
            os.remove(temp_file)
    
    # Find and remove pytest_cache directories
    pytest_dirs = []
    for root, dirs, _ in os.walk(root_dir):
        for dir in dirs:
            if ".pytest_cache" in dir or "__pytest_cache__" in dir:
                pytest_dirs.append(os.path.join(root, dir))
    
    for pytest_dir in pytest_dirs:
        if dry_run:
            print(f"Would remove directory: {pytest_dir}")
        else:
            print(f"Removing directory: {pytest_dir}")
            shutil.rmtree(pytest_dir)
    
    print(f"Found {len(temp_files)} temporary files and {len(pytest_dirs)} pytest cache directories")

def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_args()
    
    # Get project root directory
    root_dir = get_project_root()
    print(f"Project root: {root_dir}")
    
    # Clean up files
    cleanup_pycache(root_dir, args.dry_run)
    
    if not args.keep_cache:
        cleanup_cache(root_dir, args.dry_run)
    
    if not args.keep_logs:
        cleanup_logs(root_dir, args.dry_run)
    
    if not args.keep_config:
        cleanup_config(root_dir, args.dry_run)
    
    cleanup_temp_files(root_dir, args.dry_run)
    
    # Final message
    if args.dry_run:
        print("\nDRY RUN COMPLETED. No files were actually deleted.")
    else:
        print("\nCleanup completed successfully!")

if __name__ == "__main__":
    main()
