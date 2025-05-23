"""
Smart auto-selection algorithm for choosing the best music file matches.
"""
from PyQt5.QtCore import QSettings
from ..utils.logger import get_logger

logger = get_logger()


class SmartAutoSelector:
    """
    Smart auto-selection algorithm that considers multiple factors to choose the best match.
    """
    
    def __init__(self):
        """Initialize the smart auto-selector."""
        self.load_preferences()
        logger.info("Smart auto-selector initialized")
    
    def load_preferences(self):
        """Load auto-selection preferences from settings."""
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        self.enabled = settings.value("auto_select/enabled", True, type=bool)
        self.min_score = settings.value("auto_select/min_score", 80, type=int)
        self.format_preferences = settings.value("auto_select/format_preferences", 
                                                ["flac", "mp3", "m4a", "aac", "wav"])
        self.prefer_higher_bitrate = settings.value("auto_select/prefer_higher_bitrate", True, type=bool)
        self.score_tolerance = settings.value("auto_select/score_tolerance", 5, type=int)
        
        # Handle case where format_preferences is a single string
        if isinstance(self.format_preferences, str):
            self.format_preferences = [self.format_preferences]
        
        logger.info(f"Auto-selection preferences loaded: min_score={self.min_score}, "
                   f"formats={self.format_preferences}, prefer_higher_bitrate={self.prefer_higher_bitrate}")
    
    def get_format_priority(self, format_name):
        """
        Get priority index for a format (lower = higher priority).
        
        Args:
            format_name (str): Format name (e.g., 'mp3', 'flac')
        
        Returns:
            int: Priority index (0 = highest priority)
        """
        try:
            return self.format_preferences.index(format_name.lower())
        except ValueError:
            # Format not in preferences, assign lowest priority
            return len(self.format_preferences)
    
    def extract_bitrate(self, bitrate_text):
        """
        Extract numeric bitrate from text.
        
        Args:
            bitrate_text (str): Bitrate text like '320 kbps' or '320'
        
        Returns:
            int: Numeric bitrate value
        """
        if not bitrate_text:
            return 0
        
        try:
            # Remove common suffixes and extract number
            cleaned = str(bitrate_text).replace(' kbps', '').replace('kbps', '').strip()
            return int(cleaned)
        except (ValueError, TypeError):
            return 0
    
    def calculate_quality_score(self, match):
        """
        Calculate a quality score for a match based on format and bitrate preferences.
        
        Args:
            match (dict): Match dictionary containing format and bitrate info
        
        Returns:
            float: Quality score (higher = better quality preference)
        """
        quality_score = 0.0
        
        # Format preference score (0-100, higher = better)
        format_name = match.get('format', '').lower()
        format_priority = self.get_format_priority(format_name)
        max_priority = len(self.format_preferences)
        
        if max_priority > 0:
            # Convert priority to score (invert so lower priority = higher score)
            format_score = ((max_priority - format_priority) / max_priority) * 100
            quality_score += format_score * 0.7  # 70% weight for format
        
        # Bitrate preference score (0-100, higher = better)
        if self.prefer_higher_bitrate:
            bitrate = self.extract_bitrate(match.get('bitrate', 0))
            # Normalize bitrate to 0-100 scale (assuming max useful bitrate is ~500 kbps)
            bitrate_score = min(bitrate / 5.0, 100.0)  # 500 kbps = 100 points
            quality_score += bitrate_score * 0.3  # 30% weight for bitrate
        
        return quality_score
    
    def select_best_match(self, matches):
        """
        Select the best match from a list of candidates.
        
        Args:
            matches (list): List of match dictionaries
        
        Returns:
            dict or None: Best match or None if no suitable match found
        """
        if not matches or not self.enabled:
            return None
        
        # Filter matches that meet minimum score requirement
        eligible_matches = []
        for match in matches:
            match_score = match.get('combined_score', 0)
            if match_score >= self.min_score:
                eligible_matches.append(match)
        
        if not eligible_matches:
            logger.debug(f"No matches meet minimum score threshold of {self.min_score}")
            return None
        
        # Sort by match score (highest first)
        eligible_matches.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        best_match = eligible_matches[0]
        best_score = best_match.get('combined_score', 0)
        
        # Look for quality-preferred alternatives within score tolerance
        for match in eligible_matches:
            match_score = match.get('combined_score', 0)
            score_difference = best_score - match_score
            
            # If within tolerance, consider quality preferences
            if score_difference <= self.score_tolerance:
                match_quality = self.calculate_quality_score(match)
                best_quality = self.calculate_quality_score(best_match)
                
                # If this match has significantly better quality, prefer it
                if match_quality > best_quality + 10:  # 10-point quality advantage threshold
                    logger.debug(f"Preferring quality match: {match.get('filename', 'unknown')} "
                               f"(score: {match_score:.1f}, quality: {match_quality:.1f}) over "
                               f"{best_match.get('filename', 'unknown')} "
                               f"(score: {best_score:.1f}, quality: {best_quality:.1f})")
                    best_match = match
                    best_score = match_score
        
        logger.debug(f"Selected best match: {best_match.get('filename', 'unknown')} "
                    f"(score: {best_score:.1f})")
        return best_match
    
    def auto_select_from_grouped_results(self, grouped_results):
        """
        Auto-select best matches from grouped search results.
        
        Args:
            grouped_results (dict): Dictionary of grouped search results
        
        Returns:
            set: Set of file paths that should be auto-selected
        """
        if not self.enabled:
            logger.info("Auto-selection is disabled")
            return set()
        
        auto_selected = set()
        
        for key, group_data in grouped_results.items():
            matches = group_data.get('matches', [])
            
            if not matches:
                continue  # Skip groups with no matches
            
            best_match = self.select_best_match(matches)
            
            if best_match:
                file_path = best_match.get('file_path')
                if file_path:
                    auto_selected.add(file_path)
                    logger.debug(f"Auto-selected for '{group_data.get('line', 'unknown')}': "
                               f"{best_match.get('filename', 'unknown')}")
        
        logger.info(f"Auto-selected {len(auto_selected)} files from {len(grouped_results)} groups")
        return auto_selected
    
    def get_selection_summary(self, grouped_results, auto_selected_files):
        """
        Generate a summary of the auto-selection results.
        
        Args:
            grouped_results (dict): Dictionary of grouped search results
            auto_selected_files (set): Set of auto-selected file paths
        
        Returns:
            dict: Summary statistics
        """
        total_groups = len(grouped_results)
        groups_with_matches = 0
        groups_with_selections = 0
        groups_missing = 0
        groups_multiple = 0
        
        for group_data in grouped_results.values():
            matches = group_data.get('matches', [])
            match_count = len(matches)
            
            if match_count == 0:
                groups_missing += 1
            else:
                groups_with_matches += 1
                
                if match_count > 1:
                    groups_multiple += 1
                
                # Check if any match from this group was selected
                group_has_selection = any(
                    match.get('file_path') in auto_selected_files 
                    for match in matches
                )
                
                if group_has_selection:
                    groups_with_selections += 1
        
        return {
            'total_groups': total_groups,
            'groups_with_matches': groups_with_matches,
            'groups_with_selections': groups_with_selections,
            'groups_missing': groups_missing,
            'groups_multiple': groups_multiple,
            'selection_rate': (groups_with_selections / total_groups * 100) if total_groups > 0 else 0
        }
    
    def update_preferences(self, **kwargs):
        """
        Update auto-selection preferences.
        
        Args:
            **kwargs: Preference key-value pairs to update
        """
        settings = QSettings("MusicIndexer", "MusicIndexer")
        
        for key, value in kwargs.items():
            if key == 'enabled':
                self.enabled = value
                settings.setValue("auto_select/enabled", value)
            elif key == 'min_score':
                self.min_score = value
                settings.setValue("auto_select/min_score", value)
            elif key == 'format_preferences':
                self.format_preferences = value
                settings.setValue("auto_select/format_preferences", value)
            elif key == 'prefer_higher_bitrate':
                self.prefer_higher_bitrate = value
                settings.setValue("auto_select/prefer_higher_bitrate", value)
            elif key == 'score_tolerance':
                self.score_tolerance = value
                settings.setValue("auto_select/score_tolerance", value)
        
        logger.info(f"Updated auto-selection preferences: {kwargs}")


class AutoSelectionAnalyzer:
    """
    Analyzer for auto-selection results to provide insights and statistics.
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        pass
    
    def analyze_selection_quality(self, grouped_results, auto_selected_files):
        """
        Analyze the quality of auto-selection decisions.
        
        Args:
            grouped_results (dict): Dictionary of grouped search results
            auto_selected_files (set): Set of auto-selected file paths
        
        Returns:
            dict: Analysis results
        """
        analysis = {
            'total_entries': len(grouped_results),
            'entries_with_matches': 0,
            'entries_with_selections': 0,
            'average_selected_score': 0.0,
            'format_distribution': {},
            'bitrate_distribution': {},
            'score_ranges': {
                '90-100%': 0,
                '80-89%': 0,
                '70-79%': 0,
                '60-69%': 0,
                'below_60%': 0
            }
        }
        
        selected_scores = []
        format_counts = {}
        bitrate_ranges = {'0-128': 0, '128-256': 0, '256-320': 0, '320+': 0}
        
        for group_data in grouped_results.values():
            matches = group_data.get('matches', [])
            
            if matches:
                analysis['entries_with_matches'] += 1
                
                # Find selected match in this group
                selected_match = None
                for match in matches:
                    if match.get('file_path') in auto_selected_files:
                        selected_match = match
                        break
                
                if selected_match:
                    analysis['entries_with_selections'] += 1
                    
                    # Analyze selected match
                    score = selected_match.get('combined_score', 0)
                    selected_scores.append(score)
                    
                    # Score ranges
                    if score >= 90:
                        analysis['score_ranges']['90-100%'] += 1
                    elif score >= 80:
                        analysis['score_ranges']['80-89%'] += 1
                    elif score >= 70:
                        analysis['score_ranges']['70-79%'] += 1
                    elif score >= 60:
                        analysis['score_ranges']['60-69%'] += 1
                    else:
                        analysis['score_ranges']['below_60%'] += 1
                    
                    # Format distribution
                    fmt = selected_match.get('format', 'unknown').lower()
                    format_counts[fmt] = format_counts.get(fmt, 0) + 1
                    
                    # Bitrate distribution
                    bitrate = selected_match.get('bitrate', 0)
                    if isinstance(bitrate, str):
                        bitrate = int(bitrate.replace(' kbps', '').replace('kbps', '').strip() or 0)
                    
                    if bitrate <= 128:
                        bitrate_ranges['0-128'] += 1
                    elif bitrate <= 256:
                        bitrate_ranges['128-256'] += 1
                    elif bitrate <= 320:
                        bitrate_ranges['256-320'] += 1
                    else:
                        bitrate_ranges['320+'] += 1
        
        # Calculate averages and percentages
        if selected_scores:
            analysis['average_selected_score'] = sum(selected_scores) / len(selected_scores)
        
        analysis['format_distribution'] = format_counts
        analysis['bitrate_distribution'] = bitrate_ranges
        analysis['selection_percentage'] = (
            analysis['entries_with_selections'] / analysis['total_entries'] * 100
            if analysis['total_entries'] > 0 else 0
        )
        
        return analysis
    
    def generate_selection_report(self, analysis):
        """
        Generate a human-readable report from analysis results.
        
        Args:
            analysis (dict): Analysis results from analyze_selection_quality
        
        Returns:
            str: Formatted report
        """
        report = []
        report.append("Auto-Selection Analysis Report")
        report.append("=" * 35)
        report.append("")
        
        # Overview
        report.append(f"Total entries processed: {analysis['total_entries']}")
        report.append(f"Entries with matches: {analysis['entries_with_matches']}")
        report.append(f"Entries with selections: {analysis['entries_with_selections']}")
        report.append(f"Selection success rate: {analysis['selection_percentage']:.1f}%")
        report.append("")
        
        # Quality metrics
        if analysis['average_selected_score'] > 0:
            report.append(f"Average match score: {analysis['average_selected_score']:.1f}%")
            report.append("")
            
            report.append("Score Distribution:")
            for range_name, count in analysis['score_ranges'].items():
                percentage = count / analysis['entries_with_selections'] * 100 if analysis['entries_with_selections'] > 0 else 0
                report.append(f"  {range_name}: {count} ({percentage:.1f}%)")
            report.append("")
        
        # Format distribution
        if analysis['format_distribution']:
            report.append("Format Distribution:")
            for fmt, count in sorted(analysis['format_distribution'].items()):
                percentage = count / analysis['entries_with_selections'] * 100 if analysis['entries_with_selections'] > 0 else 0
                report.append(f"  {fmt.upper()}: {count} ({percentage:.1f}%)")
            report.append("")
        
        # Bitrate distribution
        if any(analysis['bitrate_distribution'].values()):
            report.append("Bitrate Distribution:")
            for range_name, count in analysis['bitrate_distribution'].items():
                percentage = count / analysis['entries_with_selections'] * 100 if analysis['entries_with_selections'] > 0 else 0
                report.append(f"  {range_name} kbps: {count} ({percentage:.1f}%)")
        
        return "\n".join(report)