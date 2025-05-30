"""
FIXED Enhanced playlist parser for complex electronic music formats.
This fixes the method binding issue you encountered.
"""
import re
from ..utils.logger import get_logger

logger = get_logger()


class EnhancedPlaylistParser:
    """
    Parse complex electronic music playlist entries.
    Handles multiple artists, remixes, and mix information.
    """
    
    def __init__(self):
        """Initialize the enhanced parser."""
        self.remix_patterns = [
            r'\s*-\s*([^-]*(?:remix|mix|edit|remaster|version)[^-]*?)$',
            r'\s*\(\s*([^)]*(?:remix|mix|edit|remaster|version)[^)]*?)\s*\)$',
        ]
        
        self.mix_keywords = {
            'remix', 'mix', 'edit', 'remaster', 'version', 'original', 'extended', 
            'radio', 'club', 'dance', 'instrumental', 'vocal', 'mashup', 'bootleg'
        }
        
        logger.info("Enhanced playlist parser initialized")
    
    def parse_complex_entry(self, line):
        """
        Parse a complex playlist entry into searchable components.
        
        Args:
            line (str): Playlist line (e.g., "Artist1, Artist2 - Title - Remix Info")
            
        Returns:
            dict: Parsed information with multiple search variations
        """
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            return None
        
        # Split on the main separator (first dash that separates artists from title)
        main_parts = self._split_main_parts(line)
        if not main_parts:
            return {'original': line, 'search_variants': [{'artist': '', 'title': line}]}
        
        artist_part = main_parts['artists']
        title_part = main_parts['title']
        remix_part = main_parts.get('remix', '')
        
        # Parse multiple artists
        artists = self._parse_multiple_artists(artist_part)
        
        # Clean title (remove remix info)
        clean_title = self._clean_title(title_part)
        
        # Create search variants
        search_variants = []
        
        # Variant 1: Primary artist + clean title
        if artists:
            search_variants.append({
                'artist': artists[0],
                'title': clean_title,
                'type': 'primary_artist'
            })
        
        # Variant 2: All artists + clean title  
        if len(artists) > 1:
            all_artists = ' '.join(artists)
            search_variants.append({
                'artist': all_artists,
                'title': clean_title,
                'type': 'all_artists'
            })
        
        # Variant 3: Artist combinations
        if len(artists) > 1:
            for i, artist in enumerate(artists):
                if i > 0:  # Skip first artist (already added)
                    search_variants.append({
                        'artist': artist,
                        'title': clean_title,
                        'type': f'artist_{i+1}'
                    })
        
        # Variant 4: Title-only search (fallback)
        search_variants.append({
            'artist': '',
            'title': clean_title,
            'type': 'title_only'
        })
        
        # Variant 5: Original line as general query
        search_variants.append({
            'artist': '',
            'title': '',
            'query': line,
            'type': 'general_query'
        })
        
        return {
            'original': line,
            'artists': artists,
            'clean_title': clean_title,
            'remix_info': remix_part,
            'search_variants': search_variants
        }
    
    def _split_main_parts(self, line):
        """
        Split line into main parts: artists, title, remix info.
        
        Args:
            line (str): Input line
            
        Returns:
            dict: Split parts or None if parsing failed
        """
        # Common separators in electronic music
        separators = [' - ', ' – ', ': ', ' : ']
        
        for separator in separators:
            if separator in line:
                parts = line.split(separator)
                
                if len(parts) >= 2:
                    artists = parts[0].strip()
                    
                    # Check if there are multiple title parts (title + remix info)
                    if len(parts) > 2:
                        # Check if last part looks like remix info
                        last_part = parts[-1].strip().lower()
                        
                        if any(keyword in last_part for keyword in self.mix_keywords):
                            # Last part is remix info
                            title = separator.join(parts[1:-1]).strip()
                            remix = parts[-1].strip()
                        else:
                            # All remaining parts are title
                            title = separator.join(parts[1:]).strip()
                            remix = ''
                    else:
                        title = parts[1].strip()
                        remix = ''
                    
                    return {
                        'artists': artists,
                        'title': title,
                        'remix': remix
                    }
        
        return None
    
    def _parse_multiple_artists(self, artist_part):
        """
        Parse multiple artists from artist string.
        
        Args:
            artist_part (str): Artist part of the line
            
        Returns:
            list: List of individual artists
        """
        if not artist_part:
            return []
        
        # Common separators for multiple artists
        separators = [', ', ' & ', ' and ', ' vs ', ' x ', ' feat ', ' ft ', ' featuring ']
        
        artists = [artist_part]  # Start with the whole string
        
        # Split by each separator
        for separator in separators:
            new_artists = []
            for artist in artists:
                if separator in artist:
                    new_artists.extend([a.strip() for a in artist.split(separator)])
                else:
                    new_artists.append(artist)
            artists = new_artists
        
        # Clean up artists
        cleaned_artists = []
        for artist in artists:
            artist = artist.strip()
            if artist and len(artist) > 1:
                cleaned_artists.append(artist)
        
        return cleaned_artists
    
    def _clean_title(self, title):
        """
        Clean title by removing remix/mix information.
        
        Args:
            title (str): Original title
            
        Returns:
            str: Cleaned title
        """
        if not title:
            return title
        
        cleaned = title
        
        # Remove remix patterns
        for pattern in self.remix_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Additional cleanup
        cleaned = re.sub(r'\s*-\s*$', '', cleaned)  # Remove trailing dash
        cleaned = re.sub(r'\s+', ' ', cleaned)      # Normalize whitespace
        cleaned = cleaned.strip()
        
        return cleaned


def enhance_auto_search_with_parser(auto_search_instance):
    """
    FIXED: Enhance the auto search instance with the new parser.
    This now properly binds methods to the instance.
    """
    
    # Create parser instance
    parser = EnhancedPlaylistParser()
    
    # Store original methods
    original_parse_match_line = auto_search_instance._parse_match_line
    original_find_matches_for_entry = auto_search_instance._find_matches_for_entry
    
    def parse_match_line_enhanced(line):
        """
        Enhanced parsing for complex playlist entries.
        """
        line = line.strip()
        
        if not line or line.startswith('#'):
            return None
        
        # Try the enhanced parser first
        parsed = parser.parse_complex_entry(line)
        
        if parsed and parsed.get('search_variants'):
            # Convert to the format expected by the original code
            original_line = parsed['original']
            
            # For compatibility, extract first artist and title
            variants = parsed['search_variants']
            first_variant = variants[0] if variants else {}
            
            artist = first_variant.get('artist', '')
            title = first_variant.get('title', original_line)
            
            return {
                'original_line': original_line,
                'artist': artist, 
                'title': title,
                'enhanced_parsed': parsed  # Store the full parsed data
            }
        else:
            # Fallback to original parsing
            return original_parse_match_line(line)
    
    def find_matches_for_entry_enhanced(parsed_info):
        """
        Enhanced matching that tries multiple search variants.
        """
        original_line = parsed_info['original_line']
        
        # Check if we have enhanced parsing data
        if 'enhanced_parsed' in parsed_info:
            enhanced_data = parsed_info['enhanced_parsed']
            search_variants = enhanced_data['search_variants']
            
            logger.debug(f"Processing enhanced: '{original_line}' with {len(search_variants)} variants")
            
            best_matches = []
            best_score = 0
            
            # Try each search variant
            for i, variant in enumerate(search_variants):
                variant_type = variant.get('type', 'unknown')
                
                if 'query' in variant:
                    # General query search
                    matches = auto_search_instance._find_matches_general_query(variant['query'])
                else:
                    # Create a query from artist + title
                    artist = variant.get('artist', '')
                    title = variant.get('title', '')
                    
                    if artist and title:
                        query = f"{artist} {title}"
                    elif artist:
                        query = artist
                    elif title:
                        query = title
                    else:
                        continue
                    
                    matches = auto_search_instance._find_matches_general_query(query)
                
                if matches:
                    current_best_score = matches[0].get('combined_score', 0)
                    
                    # Add variant info to matches
                    for match in matches:
                        match['search_variant'] = variant_type
                        match['variant_index'] = i
                    
                    if current_best_score > best_score:
                        best_matches = matches
                        best_score = current_best_score
                        logger.debug(f"Better matches with variant '{variant_type}': {current_best_score:.1f}%")
                    
                    # If we found excellent matches, stop here
                    if current_best_score >= 85:
                        logger.debug(f"Excellent matches found with variant '{variant_type}', stopping search")
                        break
            
            return best_matches
        else:
            # Use original method
            return original_find_matches_for_entry(parsed_info)
    
    # Replace the methods on the instance
    auto_search_instance._parse_match_line = parse_match_line_enhanced
    auto_search_instance._find_matches_for_entry = find_matches_for_entry_enhanced
    
    logger.info("Auto search enhanced with complex playlist parser (FIXED)")


# Test the parser with your problematic entries
def test_enhanced_parser():
    """Test the enhanced parser with actual playlist entries."""
    parser = EnhancedPlaylistParser()
    
    test_entries = [
        "Meagashira, Endymion - Who I Am",
        "Endymion - Abduction - Endymion Remix", 
        "Party Animals - Used & Abused - Amnesia Mix",
        "The Prophet, DJ Buzz Fuzz - Go Get Ill - Original Mix",
        "DJ JDA, N-Vitral - Voel Je Die Bass - N-Vitral Remix"
    ]
    
    print("🧪 TESTING ENHANCED PARSER (FIXED)")
    print("=" * 50)
    
    for entry in test_entries:
        print(f"\nOriginal: '{entry}'")
        parsed = parser.parse_complex_entry(entry)
        
        if parsed:
            print(f"Artists: {parsed['artists']}")
            print(f"Clean Title: '{parsed['clean_title']}'")
            print(f"Remix Info: '{parsed['remix_info']}'")
            print("Search Variants:")
            for variant in parsed['search_variants']:
                if 'query' in variant:
                    print(f"  - Query: '{variant['query']}' ({variant['type']})")
                else:
                    print(f"  - Artist: '{variant['artist']}' | Title: '{variant['title']}' ({variant['type']})")

if __name__ == "__main__":
    test_enhanced_parser()