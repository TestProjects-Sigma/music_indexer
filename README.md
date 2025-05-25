# Music Indexer

A Python application for indexing and searching large music collections, with support for various audio formats, intelligent auto-selection of best matches, comprehensive backup & restore capabilities, and high-performance search optimizations.

## Features

- **Multi-format Support**: Index audio files in MP3, FLAC, M4A, AAC, and WAV formats.
- **Metadata Extraction**: Extract and store information about audio files including artist, title, album, bitrate, and duration.
- **Optional Metadata Processing**: Toggle between fast indexing (basic file info only) and complete indexing (with full audio analysis).
- **Theme Support**: Choose between Light and Dark themes to customize the application appearance.
- **Flexible Search**: Two search modes:
  - **Manual Search**: Search for music by artist, title, or general query.
  - **Automatic Search**: Match music from a text file containing artist/title pairs.
- **Smart Auto-Selection**: 🆕 Automatically select the best match for each entry based on your preferences.
- **Bulk Operations**: 🆕 Copy hundreds of files with a single click after auto-selection.
- **Export Missing Tracks**: 🆕 Export unmatched tracks to text files for systematic follow-up searching.
- **Database Backup & Restore**: 🆕 Comprehensive backup system to protect your indexed music collection.
- **High-Performance Search**: 🆕 Optimized for large collections (400,000+ files) with intelligent pre-filtering and database indexing.
- **Fuzzy Matching**: Adjustable similarity threshold for flexible matching of file names and metadata.
- **Result Management**: Sort, filter, and export search results to CSV.
- **File Operations**: Copy matched files to a selected directory.
- **Cache System**: Fast indexing with SQLite-based caching of file metadata.

## 🚀 Performance Optimizations for Large Collections

The Music Indexer has been optimized to handle very large music collections efficiently:

### **Intelligent Pre-filtering**
- **Smart SQL Filtering**: Before expensive fuzzy matching, the system uses fast SQL queries to filter potential candidates
- **Keyword Extraction**: Extracts key words from search terms and matches against artist, title, and filename fields
- **Dramatic Speed Improvement**: Reduces search time from ~15 minutes to ~2-3 minutes for large collections

### **Database Indexing**
- **Optimized Indexes**: Specialized database indexes for case-insensitive LIKE queries used in pre-filtering
- **Scalable Performance**: Maintains fast search speeds even with 400,000+ indexed files
- **Automatic Index Creation**: Indexes are created automatically when the application starts

### **Performance Benchmarks**
- **Large Collection Test**: 50,000 indexed files with 31-track playlist
  - **Before optimization**: ~15 minutes
  - **After optimization**: ~2-3 minutes (5-8x speedup)
- **Expected Performance**: 400,000+ files should process playlists in under 5 minutes
- **Scalability**: Performance remains consistent as collection size grows

### **How It Works**
1. **Extract Keywords**: Break down search terms ("The Beatles - Yesterday" → ["Beatles", "Yesterday"])
2. **SQL Pre-filtering**: Use fast database queries to find candidates containing these keywords
3. **Fuzzy Matching**: Apply expensive fuzzy matching only to filtered candidates (~100-500 files instead of 400,000)
4. **Result Optimization**: Return top matches sorted by relevance score

## 🛡️ Database Backup & Restore System

### Never Lose Your Indexed Music Collection Again!
The comprehensive backup system protects weeks or months of indexing work with enterprise-level features in a user-friendly interface.

#### **🎯 Key Backup Features**
- **Multiple Archive Formats**: ZIP, TAR, TAR.GZ, and 7Z support
- **Complete Data Protection**: Backs up both your music database AND configuration settings
- **Smart Backup**: Includes your directories, preferences, auto-selection settings, and theme choices
- **Auto-naming**: Timestamp-based filenames prevent overwrites
- **Verification**: Integrity checking before restore operations
- **Metadata Tracking**: Backup files include creation info and original database statistics

#### **🔄 Restore Capabilities**
- **Safety First**: Automatically backs up existing files before restore
- **Selective Restore**: Choose whether to restore configuration along with database
- **Content Preview**: View backup contents and verify integrity before restore
- **Cross-Platform**: Move your entire music index between Windows, Mac, and Linux

#### **💾 What Gets Backed Up**
- **Music Database**: Your entire indexed music collection (thousands of files indexed in minutes on restore)
- **Configuration**: All your settings, music directories, and preferences
- **Auto-Selection Preferences**: Format priorities, quality settings, and match thresholds
- **Theme Settings**: Your chosen appearance and interface preferences
- **Directory Configurations**: No need to re-add music folders

#### **🚀 Backup Workflow Examples**

##### **Weekly Protection Routine**
```
1. Backup Tab → Quick Backup
2. Automatic timestamped backup created
3. Peace of mind - your indexed collection is safe
```

##### **Computer Migration**
```
Old Computer:
1. Backup Tab → Create Backup → Include configuration ✓
2. Save to USB drive or cloud storage

New Computer:  
1. Install Music Indexer
2. Backup Tab → Restore Backup
3. Select your backup file → Restore
4. Instantly have your entire collection indexed with all preferences!
```

##### **Before Major Changes**
```
Before upgrading or experimenting:
1. Create backup with current settings
2. Make changes safely
3. If something goes wrong: restore backup → back to working state
```

## 🚀 Smart Auto-Selection Features

### Enhanced Bulk Operations
Never manually select hundreds of tracks again! The intelligent auto-selection system can:
- **Automatically select** the best match for each playlist entry
- **Bulk copy** all selected files in one operation
- **Intelligent decision making** based on format preferences and quality

### Configurable Preferences
Customize how the system chooses matches:
- **Format Priority**: Drag-and-drop to set preferred formats (e.g., FLAC > MP3 > AAC)
- **Quality vs Score**: Prefer higher bitrate files within score tolerance
- **Minimum Threshold**: Set minimum match score for auto-selection
- **Score Tolerance**: Allow quality preference within score difference

### Enhanced Results Display
- **Checkbox selection** for individual files
- **Selection summary** showing count of selected files
- **Bulk selection controls** (select all, deselect all, auto-select best)
- **Enhanced context menus** with group operations
- **Export results** with selection status
- **Export missing tracks** 🆕 for systematic follow-up searching

## Grouped Results View
The Results panel includes a hierarchical grouped view for automatic searches from text files:

- **Organized Results**: Files are grouped by their source entry in the text file
- **Status Indicators**: 
  - ✓ Green "Found" for entries with exactly one match
  - ⚠ Orange "Multiple" for entries with multiple matches (showing the count)
  - ❌ Red "Missing" for entries with no matches
- **Expandable Groups**: Each entry can be expanded or collapsed to show/hide matching files
- **Group Operations**: Right-click context menu allows expanding or collapsing all groups
- **Auto-Selection**: 🆕 Automatically pick the best match from multiple options

## Right-Click Menu Enhancements
The results panel includes a fully-featured right-click context menu:

- **Copy Selected Files**: 🆕 Bulk copy all selected files to destination
- **Show in Folder**: Open the file's location in your system's file explorer
- **Play Audio**: Play the selected audio file with your system's default audio player
- **Export Results**: Export all results to a CSV file with selection status
- **Export Missing Tracks**: 🆕 Export unmatched tracks for follow-up searching
- **Group Operations**: Select best in group, select/deselect all in group

## Audio Playback
Audio files can be played directly from the results panel:

- **Double-Click Playback**: Double-click any file in the results to play it with your system's default audio player
- **Play from Menu**: Right-click on a file and select "Play Audio" to listen to it
- **Multiple File Support**: Select and play different audio formats including MP3, FLAC, M4A, AAC, and WAV

## Performance Optimization
Enhanced indexing options for improved performance:

- **Fast Indexing Mode**: Skip audio metadata extraction for significantly faster indexing
- **Toggle Controls**: Easily switch between fast indexing and full audio analysis
- **Smart Caching**: Files indexed with basic info can be updated later with full metadata
- **Progress Indicators**: Clear indication of which extraction mode is being used
- **Bulk Operations**: 🆕 Non-blocking file operations with progress tracking
- **Incremental Updates**: 🆕 Subsequent indexing runs only process new/changed files
- **Intelligent Search**: 🆕 Pre-filtering and database indexing for large collections

## Theme Support
The application supports multiple visual themes:

- **Dark Theme**: A modern dark interface for comfortable use in low-light environments
- **Light Theme**: A clean, bright interface for high-visibility usage
- **System Default**: Uses your operating system's native look and feel
- **Persistent Settings**: Your theme preference is saved between sessions and included in backups

## Enhanced Search Results
The automatic search feature provides comprehensive visibility and follow-up capabilities:

- **Missing Track Detection**: Clearly see which entries from your text file have no matching files
- **Export Missing Tracks**: 🆕 Export unmatched tracks to text files for systematic hunting and re-processing
- **Match Statistics**: View counts of found, missing, and multiple matches in the status bar
- **Selection Analytics**: 🆕 Track auto-selection success rates and quality metrics
- **Enhanced CSV Export**: Export results with hierarchical information including match status and selection state
- **Workflow Completion**: 🆕 Complete cycle from search → export missing → add music → re-search → improve success rate

## Spotify Integration
The Music Indexer includes a dedicated Spotify tab for extracting playlists:

- **Playlist Extraction**: Extract tracks from any public Spotify playlist using the playlist URL
- **Spotify API Support**: Connect using your Spotify API credentials (Client ID and Secret)
- **Credential Management**: Securely save your Spotify credentials for future sessions
- **Format Compatibility**: Extracted playlists are saved in the correct format for automatic searching
- **Guided Workflow**: Step-by-step instructions help you find matches for your Spotify playlists

## Requirements

- Python 3.6+
- PyQt5
- Mutagen
- FuzzyWuzzy
- Python-Levenshtein
- tqdm
- requests (for Spotify integration)

## Installation

1. Clone this repository or download the source code.
2. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python main.py
```

### Initial Setup

1. Go to the "Settings" tab and add your music directories.
2. Click "Index Files" to scan and index your music collection.
   - Use the "Extract Audio Metadata" checkbox to toggle between fast and complete indexing
3. **Create Your First Backup** 🆕:
   - Go to the "Backup" tab
   - Click "Quick Backup" or customize backup settings
   - Your indexed collection is now protected!
4. **Configure Auto-Selection Preferences** 🆕:
   - Set your preferred format order (drag and drop to reorder)
   - Choose minimum match score threshold
   - Enable/disable higher bitrate preference
   - Adjust score tolerance for quality vs accuracy trade-offs
5. Choose your preferred theme in the Appearance section.

### Database Backup & Restore 🆕

#### Creating Backups
1. **Navigate to Backup Tab**: Click the "Backup" tab in the main interface
2. **Review Database Info**: See your current indexed files count and database size
3. **Choose Format**: Select ZIP (recommended), TAR.GZ, TAR, or 7Z
4. **Select Options**: 
   - ✅ Include configuration (recommended) - preserves all your settings
   - Choose backup location or use auto-generated filename
5. **Create Backup**: Click "Create Backup" or "Quick Backup" for default settings

#### Restoring Backups
1. **Select Backup File**: Browse to your backup archive
2. **Choose Options**:
   - Restore configuration (includes all your preferences and settings)
   - Backup existing files (safety measure - recommended)
3. **Verify First** (Optional): Click "Verify Backup Integrity" to check the backup
4. **Restore**: Click "Restore Backup" - your entire indexed collection will be restored

#### Quick Actions
- **Quick Backup**: One-click backup with optimal settings
- **Open Backup Folder**: Direct access to your backup directory
- **Auto-Generate Filename**: Timestamp-based naming to prevent overwrites

### Searching Music

#### Manual Search

1. Select "Manual Search" in the Search tab.
2. Enter search criteria (artist, title, or general query).
3. Select whether to use exact or fuzzy matching.
4. Click "Search" to find matching files.
5. **Use checkboxes** to select files you want to copy.

#### Automatic Search from File (🆕 Enhanced Workflow)

1. Select "Automatic Search" in the Search tab.
2. Choose a text file containing artist/title pairs (one per line).
3. Adjust similarity threshold as needed.
4. Click "Process File" to find matches for all entries.
5. **Click "Auto-Select Best Matches"** to automatically choose the best file for each entry.
6. **Review and adjust selections** using checkboxes if needed.
7. **Click "Copy Selected Files"** to bulk copy all selected files.
8. **Export Missing Tracks** 🆕 to get a text file of unmatched entries for follow-up.

### Enhanced Working with Results

#### Smart Auto-Selection (🆕)
- **Auto-Select Best Matches**: Automatically selects the highest quality match for each playlist entry
- **Bulk Selection**: Select all matches, deselect all, or use smart selection
- **Selection Summary**: See how many files are currently selected

#### File Operations
- **Bulk Copy**: Copy all selected files to a destination folder in one operation
- **Export Missing**: 🆕 Export unmatched tracks to text files for systematic follow-up
- **Individual Actions**: Show in folder, play audio, or manually select/deselect
- **Progress Tracking**: Non-blocking copy operations with real-time progress

#### Quality Control
- **Format Preferences**: System respects your preferred audio formats
- **Bitrate Optimization**: Automatically prefer higher quality files when scores are similar
- **Score Thresholds**: Only auto-select files that meet your minimum quality standards

### Missing Track Follow-up Workflow 🆕

#### Systematic Missing Track Resolution
```
1. Run automatic search on playlist
2. Auto-select best matches for found tracks
3. Copy matched files to destination
4. Export Missing Tracks to text file
5. Hunt down missing music (buy, download, find)
6. Add new music to collection and re-index
7. Use exported missing tracks file for new automatic search
8. Repeat until 100% playlist completion!
```

#### Export Missing Tracks Features
- **Smart Detection**: Automatically identifies tracks with no matches
- **Reusable Format**: Exported file works directly with automatic search
- **Multiple Formats**: TXT (default) or CSV with detailed information
- **Statistics Tracking**: See your success rate improve over time
- **Workflow Integration**: Seamlessly fits into the search → match → export → follow-up cycle

### Data Protection Best Practices 🛡️

#### Regular Backup Schedule
```
Weekly: Quick Backup to local storage
Monthly: Full backup to cloud storage or external drive
Before major changes: Create backup with descriptive name
```

#### Migration Strategy
```
Moving computers: 
1. Create backup with configuration
2. Install Music Indexer on new system
3. Restore backup
4. Verify all settings and directories
```

#### Recovery Planning
```
System crash recovery:
1. Reinstall Music Indexer
2. Restore from most recent backup
3. Verify database integrity
4. Resume normal operations
```

### Auto-Selection Configuration Examples

#### High-Quality Setup
```
Format Preferences: FLAC > WAV > M4A > MP3 > AAC
Minimum Score: 85%
Score Tolerance: 3%
Prefer Higher Bitrate: Yes
```

#### Balanced Setup
```
Format Preferences: MP3 > FLAC > M4A > AAC > WAV
Minimum Score: 75%
Score Tolerance: 5%
Prefer Higher Bitrate: Yes
```

#### Compatibility-First Setup
```
Format Preferences: MP3 > M4A > AAC > FLAC > WAV
Minimum Score: 70%
Score Tolerance: 10%
Prefer Higher Bitrate: No
```

## Match File Format

The automatic search accepts text files with the following format:

```
Artist - Title
Another Artist - Another Title
# Comments start with #
```

Supported separators between artist and title:
- " - " (space, dash, space)
- " – " (space, em dash, space)
- ": " (colon, space)
- " : " (colon, space)
- "_-_" (underscore, dash, underscore)
- "," (comma)

## Project Structure

```
music_indexer/
├── main.py                      # Main application entry point
├── music_indexer/
│   ├── __init__.py              # Package initialization
│   ├── core/                    # Core functionality
│   │   ├── file_scanner.py      # File scanning functionality
│   │   ├── metadata_extractor.py # Audio metadata extraction
│   │   └── cache_manager.py     # SQLite-based caching with performance optimizations
│   ├── search/                  # Search functionality
│   │   ├── manual_search.py     # Manual search implementation
│   │   ├── auto_search.py       # Automatic search from file with pre-filtering
│   │   └── string_matcher.py    # Fuzzy string matching with performance optimizations
│   ├── gui/                     # GUI components
│   │   ├── main_window.py       # Main application window
│   │   ├── search_panel.py      # Search interface
│   │   ├── results_panel.py     # Enhanced results display and management
│   │   ├── settings_panel.py    # Application settings interface
│   │   ├── spotify_panel.py     # Spotify integration
│   │   └── backup_panel.py      # 🆕 Database backup and restore interface
│   └── utils/                   # Utility modules
│       ├── config_manager.py    # Configuration management
│       ├── logger.py            # Logging functionality
│       ├── smart_auto_selector.py # Smart auto-selection algorithm
│       └── backup_manager.py    # 🆕 Backup and restore operations
└── tests/                       # Unit tests
    ├── test_file_scanner.py     # Tests for file scanner
    ├── test_metadata_extractor.py # Tests for metadata extraction
    └── test_string_matcher.py   # Tests for string matching
```

## Troubleshooting

### Common Issues

- **No Files Found**: Ensure your music directories are correctly configured in Settings.
- **Slow Indexing**: For large collections, use the "Extract Audio Metadata" option to toggle faster indexing without audio analysis.
- **Match Quality**: Adjust the similarity threshold in the Settings or Search tab if matches are too strict or too loose.
- **Auto-Selection Not Working**: 🆕 Check that auto-selection is enabled in Settings and that your minimum score threshold isn't too high.
- **Poor Auto-Selection Results**: 🆕 Adjust format preferences and score tolerance in Settings to better match your collection and preferences.
- **Bulk Copy Failures**: 🆕 Ensure destination folder exists and you have write permissions. Check logs for specific error details.
- **Missing Tracks Export Empty**: 🆕 This means all tracks were found! Check that you ran an automatic search (not manual search) to get missing track export option.
- **Backup Creation Fails**: 🆕 Ensure you have write permissions to the backup destination and sufficient disk space.
- **Restore Operation Fails**: 🆕 Verify backup integrity first, ensure the application has write permissions to database location.
- **Theme Not Applying**: If the theme doesn't change immediately, try saving settings and restarting the application.
- **Slow Search Performance**: 🆕 Large collections benefit from the optimized search system. Ensure you're using the latest version with pre-filtering enabled.

### Performance Tips

- **Large Collections**: Use fast indexing mode for initial setup, then re-index with full metadata when needed
- **Large Playlists**: The optimized search system handles thousands of entries efficiently
- **Network Storage**: Local storage performs better than network-attached storage for bulk operations
- **Regular Backups**: 🆕 Create backups regularly - they're much faster than re-indexing large collections
- **Incremental Indexing**: 🆕 Subsequent indexing runs are much faster as they only process new/changed files
- **Missing Track Workflow**: 🆕 Use export missing tracks feature to systematically improve playlist completion rates
- **Batch Processing**: 🆕 Process multiple playlists, export missing tracks from each, then hunt for all missing music at once
- **Search Optimization**: 🆕 The system automatically uses optimized search algorithms for collections larger than 5,000 files

### Data Protection

- **Backup Before Major Changes**: Always create a backup before upgrading, changing settings, or moving files
- **Verify Backups**: Use the "Verify Backup Integrity" feature to ensure your backups are valid
- **Multiple Backup Locations**: Store backups in different locations (local, cloud, external drive) for maximum protection
- **Test Restores**: Periodically test restore operations to ensure your backup strategy works

### Logs

Logs are stored in the `logs` directory and include detailed information about:
- Auto-selection decisions and reasoning
- File copy operations and any failures
- Match quality statistics and performance metrics
- Backup and restore operations with detailed success/failure information
- Search performance metrics and pre-filtering statistics 🆕

## License

This project is open source and available under the MIT License.

## Acknowledgements

- [Mutagen](https://mutagen.readthedocs.io/) for audio metadata extraction
- [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy) for fuzzy string matching
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [SQLite](https://www.sqlite.org/) for the database engine
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) for playlist integration

## Recent Updates

### Version 0.4.0 - High-Performance Search Optimizations
- 🆕 **Intelligent Pre-filtering**: SQL-based candidate filtering before fuzzy matching for massive speed improvements
- 🆕 **Database Indexing**: Specialized indexes for case-insensitive LIKE queries used in search optimization
- 🆕 **Large Collection Support**: Optimized for collections with 400,000+ files
- 🆕 **Performance Benchmarks**: 5-8x speedup on large collection searches
- 🆕 **Keyword Extraction**: Smart extraction of search terms for efficient pre-filtering
- 🆕 **Scalable Architecture**: Maintains fast performance regardless of collection size

### Version 0.3.0 - Database Backup & Restore System + Missing Track Export
- 🆕 **Export Missing Tracks**: Export unmatched playlist entries to text files for systematic follow-up
- 🆕 **Complete Workflow**: Search → match → copy → export missing → hunt → repeat until 100% completion
- 🆕 **Reusable Format**: Exported missing tracks files work directly with automatic search
- 🆕 **Success Rate Tracking**: See statistics and improve playlist completion over time
- 🆕 **Comprehensive Backup System**: Full database and configuration backup with multiple archive formats
- 🆕 **Smart Restore Operations**: Safe restore with automatic backup of existing files
- 🆕 **Backup Verification**: Integrity checking and content preview for backup files
- 🆕 **Cross-Platform Migration**: Easy transfer of indexed collections between computers
- 🆕 **Data Protection**: Never lose weeks of indexing work again
- 🆕 **Quick Backup Actions**: One-click backup creation with optimal settings
- 🆕 **Incremental Indexing**: Much faster subsequent indexing runs (only processes new/changed files)

### Version 0.2.0 - Enhanced Auto-Selection
- 🆕 **Smart Auto-Selection**: Automatically select best matches based on configurable preferences
- 🆕 **Bulk Operations**: Copy hundreds of files with single-click operations
- 🆕 **Format Preferences**: Drag-and-drop format priority configuration
- 🆕 **Quality vs Score Trade-offs**: Intelligent decision making within score tolerance
- 🆕 **Enhanced Results Panel**: Checkbox selection, bulk controls, selection analytics
- 🆕 **Improved Settings**: Comprehensive auto-selection preference configuration
- 🆕 **Selection Analytics**: Track auto-selection success rates and quality metrics
- ✨ **Performance**: Non-blocking file operations with progress tracking
- ✨ **Usability**: Streamlined workflow for large playlist processing

Perfect for users with large music collections who need to efficiently match and copy files from playlists with hundreds of tracks, while ensuring their indexed database is always protected and portable! 🎵🛡️⚡

## 🎯 Why Choose Music Indexer?

- **🚀 Speed**: Index once, search instantly - optimized for collections up to 400,000+ files
- **🧠 Intelligence**: Smart auto-selection saves hours of manual work
- **🛡️ Protection**: Enterprise-level backup system protects your work
- **🔄 Portability**: Move your entire indexed collection between computers effortlessly
- **🎵 Scale**: Handle massive collections with optimized search algorithms
- **⚙️ Flexibility**: Customize every aspect of matching and selection behavior
- **📋 Completeness**: 🆕 Export missing tracks for systematic playlist completion
- **🔁 Workflow**: 🆕 Complete cycle from search to 100% playlist matching
- **⚡ Performance**: 🆕 Advanced optimizations deliver 5-8x speedup on large collections

Transform your music collection management from tedious manual work to automated efficiency with systematic missing track resolution and blazing-fast search performance for any collection size!