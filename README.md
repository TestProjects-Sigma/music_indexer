# Music Indexer

A Python application for indexing and searching large music collections, with support for various audio formats and flexible matching algorithms.

## Features

- **Multi-format Support**: Index audio files in MP3, FLAC, M4A, AAC, and WAV formats.
- **Metadata Extraction**: Extract and store information about audio files including artist, title, album, bitrate, and duration.
- **Flexible Search**: Two search modes:
  - **Manual Search**: Search for music by artist, title, or general query.
  - **Automatic Search**: Match music from a text file containing artist/title pairs.
- **Fuzzy Matching**: Adjustable similarity threshold for flexible matching of file names and metadata.
- **Result Management**: Sort, filter, and export search results to CSV.
- **File Operations**: Copy matched files to a selected directory.
- **Cache System**: Fast indexing with SQLite-based caching of file metadata.

## Grouped Results View
The Results panel now includes a hierarchical grouped view for automatic searches from text files:

- **Organized Results**: Files are grouped by their source entry in the text file
- **Status Indicators**: 
  - ✓ Green "Found" for entries with exactly one match
  - ⚠ Orange "Multiple" for entries with multiple matches (showing the count)
  - ❌ Red "Missing" for entries with no matches
- **Expandable Groups**: Each entry can be expanded or collapsed to show/hide matching files
- **Group Operations**: Right-click context menu allows expanding or collapsing all groups

## Right-Click Menu Enhancements
The results panel now includes a fully-featured right-click context menu:

- **Copy to Export Folder**: Copy selected files directly to the configured export directory
- **Show in Folder**: Open the file's location in your system's file explorer
- **Play Audio**: Play the selected audio file with your system's default audio player
- **Export Results**: Export all results to a CSV file

## Audio Playback
Audio files can now be played directly from the results panel:

- **Double-Click Playback**: Double-click any file in the results to play it with your system's default audio player
- **Play from Menu**: Right-click on a file and select "Play Audio" to listen to it
- **Multiple File Support**: Select and play different audio formats including MP3, FLAC, M4A, AAC, and WAV

## Enhanced Search Results
The automatic search feature now provides better visibility:

- **Missing Track Detection**: Clearly see which entries from your text file have no matching files
- **Match Statistics**: View counts of found, missing, and multiple matches in the status bar
- **Enhanced CSV Export**: Export results with hierarchical information including match status

## Spotify Integration
The Music Indexer now includes a dedicated Spotify tab for extracting playlists:

- **Playlist Extraction**: Extract tracks from any public Spotify playlist using the playlist URL
- **Spotify API Support**: Connect using your Spotify API credentials (Client ID and Secret)
- **Credential Management**: Securely save your Spotify credentials for future sessions
- **Format Compatibility**: Extracted playlists are saved in the correct format for automatic searching
- **Guided Workflow**: Step-by-step instructions help you find matches for your Spotify playlists

## Grouped Results View
The Results panel now includes a hierarchical grouped view for automatic searches:

- **Organized Results**: Files are grouped by their source entry in the text file
- **Status Indicators**: 
  - ✓ Green "Found" for entries with exactly one match
  - ⚠ Orange "Multiple" for entries with multiple matches (showing the count)
  - ❌ Red "Missing" for entries with no matches
- **Expandable Groups**: Each entry can be expanded or collapsed to show/hide matching files
- **Group Operations**: Right-click context menu allows expanding or collapsing all groups

## Right-Click Menu Enhancements
The results panel now includes a fully-featured right-click context menu:

- **Copy to Export Folder**: Copy selected files directly to the configured export directory
- **Show in Folder**: Open the file's location in your system's file explorer
- **Play Audio**: Play the selected audio file with your system's default audio player
- **Export Results**: Export all results to a CSV file

## Audio Playback
Audio files can now be played directly from the results panel:

- **Double-Click Playback**: Double-click any file in the results to play it with your system's default audio player
- **Play from Menu**: Right-click on a file and select "Play Audio" to listen to it
- **Multiple File Support**: Select and play different audio formats including MP3, FLAC, M4A, AAC, and WAV

## Enhanced Search Results
The automatic search feature now provides better visibility:

- **Missing Track Detection**: Clearly see which entries from your text file have no matching files
- **Match Statistics**: View counts of found, missing, and multiple matches in the status bar
- **Enhanced CSV Export**: Export results with hierarchical information including match status

## Getting Started with Spotify Integration

1. **Get Spotify API Credentials**:
   - Create an account at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Create a new application to get your Client ID and Client Secret

2. **Using the Spotify Tab**:
   - Enter the URL of a public Spotify playlist
   - Provide your Spotify API credentials
   - Select the output file location
   - Click "Extract Playlist"

3. **Finding Matches**:
   - After extraction, go to the Search tab
   - Select "Automatic Search"
   - Browse and select your extracted playlist file
   - Click "Process File" to find matches in your music collection


## Requirements

- Python 3.6+
- PyQt5
- Mutagen
- FuzzyWuzzy
- Python-Levenshtein
- tqdm

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
3. Adjust search settings like similarity threshold as needed.

### Searching Music

#### Manual Search

1. Select "Manual Search" in the Search tab.
2. Enter search criteria (artist, title, or general query).
3. Select whether to use exact or fuzzy matching.
4. Click "Search" to find matching files.

#### Automatic Search from File

1. Select "Automatic Search" in the Search tab.
2. Choose a text file containing artist/title pairs (one per line).
3. Adjust similarity threshold as needed.
4. Click "Process File" to find matches for all entries.

### Working with Results

- View search results in the Results tab.
- Sort results by clicking on column headers.
- Select files to copy to a destination folder.
- Export results to CSV for further analysis.

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
- "_-_" (underscore, dash, underscore)

## Project Structure

```
music_indexer/
├── main.py                      # Main application entry point
├── music_indexer/
│   ├── __init__.py              # Package initialization
│   ├── core/                    # Core functionality
│   │   ├── file_scanner.py      # File scanning functionality
│   │   ├── metadata_extractor.py # Audio metadata extraction
│   │   └── cache_manager.py     # SQLite-based caching
│   ├── search/                  # Search functionality
│   │   ├── manual_search.py     # Manual search implementation
│   │   ├── auto_search.py       # Automatic search from file
│   │   └── string_matcher.py    # Fuzzy string matching
│   ├── gui/                     # GUI components
│   │   ├── main_window.py       # Main application window
│   │   ├── search_panel.py      # Search interface
│   │   ├── results_panel.py     # Results display and management
│   │   └── settings_panel.py    # Application settings interface
│   └── utils/                   # Utility modules
│       ├── config_manager.py    # Configuration management
│       └── logger.py            # Logging functionality
└── tests/                       # Unit tests
    ├── test_file_scanner.py     # Tests for file scanner
    ├── test_metadata_extractor.py # Tests for metadata extraction
    └── test_string_matcher.py   # Tests for string matching
```

## Filename Parsing

The application can extract artist and title information from various filename formats:

- "Artist - Song"
- "Artist_-_Song"
- "Artist_Song"
- "01 - Artist - Song"
- "01_-_Artist_-_Song"
- "Song - Artist"
- "Song_-_Artist"
- "Song_Artist"
- "01 - Song - Artist"
- "01_-_Song_-_Artist"

## Cache Management

The application uses an SQLite database for caching file metadata. This significantly speeds up subsequent searches without requiring a full rescan.

- **Cache Location**: By default, the cache is stored in the `cache/music_cache.db` file.
- **Cache Clearing**: You can clear the cache from the main window or the Edit menu.
- **Cache Statistics**: The status bar shows statistics about the cached files.

## Development

### Adding New Features

To extend the application with new features:

1. **Add New File Formats**: Extend the `MetadataExtractor` class in `metadata_extractor.py`.
2. **Improve Matching Algorithm**: Modify the `StringMatcher` class in `string_matcher.py`.
3. **Add New Search Functionality**: Create new search methods in the search modules.

### Running Tests

Run the test suite to ensure everything is working correctly:

```bash
# From the project root directory
pytest tests/
```

## Troubleshooting

### Common Issues

- **No Files Found**: Ensure your music directories are correctly configured in Settings.
- **Slow Indexing**: For large collections, indexing may take some time on first run. Subsequent runs will be faster due to caching.
- **Match Quality**: Adjust the similarity threshold in the Settings or Search tab if matches are too strict or too loose.

### Logs

Logs are stored in the `logs` directory and can be useful for troubleshooting issues.

## License

This project is open source and available under the MIT License.

## Acknowledgements

- [Mutagen](https://mutagen.readthedocs.io/) for audio metadata extraction
- [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy) for fuzzy string matching
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [SQLite](https://www.sqlite.org/) for the database engine
"# music_indexer" 
