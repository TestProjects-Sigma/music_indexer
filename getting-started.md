# Music Indexer - Getting Started Guide

This guide will help you set up and use the Music Indexer application step-by-step.

## Installation

### Prerequisites

Before installing Music Indexer, make sure you have:

- Python 3.6 or newer installed on your system
- Basic familiarity with running Python applications

### Setup Steps

1. **Download the code** or clone the repository:
   ```bash
   git clone https://github.com/yourusername/music-indexer.git
   cd music-indexer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## Quick Start Guide

### First Launch

When you launch Music Indexer for the first time, follow these steps:

1. **Configure Music Directories**:
   - Go to the "Settings" tab
   - Click "Add Directory" and select folders containing your music files
   - You can add multiple directories from different locations/drives

2. **Index Your Music**:
   - Click the "Index Files" button on the main window
   - Wait for the indexing process to complete (this may take some time for large collections)
   - The status bar will show progress and statistics

3. **Adjust Settings** (optional):
   - Set your preferred similarity threshold (higher values require closer matches)
   - Select which file formats to include in searches
   - Enable/disable recursive directory scanning

### Basic Searching

#### Manual Search

For quick searches of your music collection:

1. Go to the "Search" tab
2. Select "Manual Search" mode
3. Enter your search terms:
   - General query: searches across all fields
   - Artist: searches specifically for artist names
   - Title: searches specifically for song titles
   - Format: filter by file format (mp3, flac, etc.)
4. Choose whether to use exact matching or fuzzy matching
5. Click "Search" to see results

#### Automatic Search

For batch searching multiple songs from a text file:

1. Create a text file with artist/title pairs, one per line:
   ```
   Radiohead - Karma Police
   The Beatles - Yesterday
   Queen - Bohemian Rhapsody
   ```

2. In the "Search" tab, select "Automatic Search" mode
3. Click "Browse" and select your text file
4. Adjust the similarity threshold slider if needed
5. Click "Process File" to find matches for all entries

### Working with Results

After performing a search:

1. Results appear in the "Results" tab
2. You can:
   - Sort results by clicking column headers
   - Select multiple files using Ctrl/Shift + click
   - Show selected files in their folder with "Show in Folder"
   - Copy selected files to a new location with "Copy to Folder"
   - Export all results to a CSV file with "Export Results"

## Example Workflow

Here's a typical workflow example:

1. Add all your music directories in Settings
2. Index your collection
3. Create a text file with songs you want to find
4. Use Automatic Search to process the file
5. Review matches in the Results tab
6. Export results or copy matched files to a new folder

## Tips and Tricks

- **For Better Matches**: If you're not getting good matches, try:
  - Lowering the similarity threshold (especially for non-English names)
  - Simplifying artist names (e.g., use "Beatles" instead of "The Beatles")
  - Using partial information in manual search

- **Performance**: 
  - The first index operation will be slow, but subsequent operations are much faster
  - Consider limiting the music directories to manageable sizes
  - Clear and rebuild the cache if you experience strange behavior

- **Match File Format**:
  - You can add comments in your match file by starting lines with #
  - The application supports various separator formats between artist and title

- **Keyboard Shortcuts**:
  - Ctrl+I: Index Files
  - Ctrl+Q: Exit Application

## Troubleshooting

### Common Issues

1. **Application starts but no files are found**
   - Check if you've added music directories in Settings
   - Verify that the directories contain supported audio formats
   - Ensure recursive scanning is enabled if your files are in subdirectories

2. **Search returns no results**
   - Check if indexing completed successfully
   - Try lowering the similarity threshold
   - Try simpler search terms
   - Check if your audio files have metadata or filename structures the app can parse

3. **Application is slow**
   - For very large collections, indexing and searching can take longer
   - Consider indexing smaller subsets of your collection
   - Make sure your system meets the minimum requirements

### Getting Help

If you encounter problems:

1. Check the logs in the `logs` directory
2. Review the README file for documentation
3. Submit issues through the project's issue tracker

## Next Steps

Once you're comfortable with basic usage, explore:

- Creating complex match files for batch processing
- Adjusting settings for optimal matching performance
- Contributing to the project by extending functionality
