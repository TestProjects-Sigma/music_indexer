"""
Spotify playlist extractor utility.
Adapted from the original spotify_playlist_extractor.py script.
"""
import re
import requests
import base64
import configparser
import os
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger()


class SpotifyPlaylistExtractor:
    """Extract tracks from a Spotify playlist."""
    
    def __init__(self, client_id=None, client_secret=None, config_manager=None):
        """
        Initialize the Spotify playlist extractor.
        
        Args:
            client_id (str): Spotify API client ID
            client_secret (str): Spotify API client secret
            config_manager: Optional config manager from the main app
        """
        # Spotify API credentials
        self.client_id = client_id or ""
        self.client_secret = client_secret or ""
        self.token = None
        self.is_extracting = False
        self.config_manager = config_manager
        self.config_file = os.path.join(str(Path.home()), ".spotify_extractor_config.ini")
        
        # Load credentials if available and not provided
        if not (client_id and client_secret):
            self.load_credentials()

    def load_credentials(self):
        """Load credentials from config file if it exists."""
        try:
            if self.config_manager:
                # Use music indexer's config manager
                self.client_id = self.client_id or self.config_manager.get("spotify", "client_id", "")
                self.client_secret = self.client_secret or self.config_manager.get("spotify", "client_secret", "")
            else:
                # Fallback to original method
                if os.path.exists(self.config_file):
                    config = configparser.ConfigParser()
                    config.read(self.config_file)
                    if 'Spotify' in config:
                        self.client_id = self.client_id or config['Spotify'].get('client_id', '')
                        self.client_secret = self.client_secret or config['Spotify'].get('client_secret', '')
        except Exception as e:
            logger.error(f"Error loading Spotify credentials: {str(e)}")
            # If there's any error reading the config, just use empty credentials
            pass

    def save_credentials(self, client_id=None, client_secret=None):
        """
        Save credentials to config file.
        
        Args:
            client_id (str): Spotify API client ID
            client_secret (str): Spotify API client secret
        
        Returns:
            bool: True if credentials were saved successfully, False otherwise
        """
        try:
            # Use provided credentials or existing ones
            save_client_id = client_id or self.client_id
            save_client_secret = client_secret or self.client_secret
            
            if self.config_manager:
                # Use music indexer's config manager
                self.config_manager.set("spotify", "client_id", save_client_id)
                self.config_manager.set("spotify", "client_secret", save_client_secret)
                return True
            else:
                # Fallback to original method
                config = configparser.ConfigParser()
                config['Spotify'] = {
                    'client_id': save_client_id,
                    'client_secret': save_client_secret
                }
                with open(self.config_file, 'w') as f:
                    config.write(f)
                return True
        except Exception as e:
            logger.error(f"Error saving Spotify credentials: {str(e)}")
            return False
    
    def authenticate(self):
        """
        Get Spotify API access token.
        
        Returns:
            tuple: (success, message)
        """
        # Validate credentials
        if not self.client_id or not self.client_secret:
            return False, "Missing Spotify API credentials"
        
        auth_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            self.token = response.json()["access_token"]
            return True, "Authentication successful"
        except requests.exceptions.RequestException as e:
            return False, f"Authentication error: {str(e)}"
    
    def extract_playlist_id(self, playlist_url):
        """
        Extract playlist ID from Spotify URL.
        
        Args:
            playlist_url (str): Spotify playlist URL
        
        Returns:
            str: Playlist ID or None if not found
        """
        pattern = r'spotify\.com/playlist/([a-zA-Z0-9]+)'
        match = re.search(pattern, playlist_url)
        if match:
            return match.group(1)
        return None
    
    def get_playlist_tracks(self, playlist_id, callback=None):
        """
        Get all tracks from a playlist.
        
        Args:
            playlist_id (str): Spotify playlist ID
            callback (function): Optional callback function to report progress
        
        Returns:
            list: List of tracks with artist and title information
        """
        # Authenticate if no token
        if not self.token:
            success, message = self.authenticate()
            if not success:
                if callback:
                    callback(False, message)
                return []
        
        tracks = []
        next_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            while next_url and self.is_extracting:
                response = requests.get(next_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                for item in data["items"]:
                    if item["track"]:
                        track_name = item["track"]["name"]
                        artists = ", ".join([artist["name"] for artist in item["track"]["artists"]])
                        tracks.append({"track": track_name, "artists": artists})
                
                # Update progress if callback provided
                if callback:
                    callback(True, f"Retrieved {len(tracks)} tracks so far...")
                
                # Get next page of results
                next_url = data.get("next")
            
            return tracks
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tracks: {str(e)}")
            if callback:
                callback(False, f"Error fetching tracks: {str(e)}")
            return []
    
    def save_to_file(self, tracks, file_path):
        """
        Save tracks to file.
        
        Args:
            tracks (list): List of track dictionaries
            file_path (str): Output file path
        
        Returns:
            tuple: (success, message)
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for track in tracks:
                    f.write(f"{track['artists']} - {track['track']}\n")
            return True, f"Successfully saved {len(tracks)} tracks to {file_path}"
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return False, f"Error saving file: {str(e)}"
    
    def extract_playlist(self, playlist_url, output_file, callback=None):
        """
        Extract playlist tracks and save to file.
        
        Args:
            playlist_url (str): Spotify playlist URL
            output_file (str): Output file path
            callback (function): Optional callback function to report progress
        
        Returns:
            tuple: (success, message)
        """
        self.is_extracting = True
        
        # Extract playlist ID
        playlist_id = self.extract_playlist_id(playlist_url)
        if not playlist_id:
            if callback:
                callback(False, "Invalid Spotify playlist URL")
            return False, "Invalid Spotify playlist URL"
        
        # Get tracks
        tracks = self.get_playlist_tracks(playlist_id, callback)
        
        # Stop if extraction was cancelled
        if not self.is_extracting:
            if callback:
                callback(False, "Extraction cancelled")
            return False, "Extraction cancelled"
        
        if not tracks:
            if callback:
                callback(False, "No tracks found or error occurred")
            return False, "No tracks found or error occurred"
        
        # Save to file
        return self.save_to_file(tracks, output_file)
    
    def cancel_extraction(self):
        """Cancel ongoing extraction."""
        self.is_extracting = False
