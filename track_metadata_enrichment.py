#!/usr/bin/env python3
"""
Track Metadata Enrichment Script for DJ Playlists

This script enriches audio files with missing metadata (genre, year, mood)
by querying online music databases like MusicBrainz, Last.fm, and Discogs.
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from mutagen import File
from mutagen.m4a import M4A
from mutagen.easyid3 import EasyID3
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('metadata_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
API_KEYS_PATH = "api_keys.json"
FILE_FORMAT = "mp3"
WORKERS = 4

class MetadataEnricher:
    """Main class for enriching track metadata"""
    
    def __init__(self, api_keys: Dict = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TrackMetadataEnricher/1.0 (DJ Playlist Tool)'
        })
        
        # API endpoints
        self.musicbrainz_url = "https://musicbrainz.org/ws/2"
        self.lastfm_url = "http://ws.audioscrobbler.com/2.0/"
        self.discogs_url = "https://api.discogs.com"
        
        # API keys
        self.api_keys = api_keys or {}
        self.lastfm_api_key = self.api_keys.get('lastfm_api_key', '')
        self.discogs_token = self.api_keys.get('discogs_token', '')
        self.spotify_client_id = self.api_keys.get('spotify_client_id', '')
        self.spotify_client_secret = self.api_keys.get('spotify_client_secret', '')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
        
        # Check API key availability
        self.check_api_keys()
        
    def check_api_keys(self):
        """Check which API keys are available and log status"""
        available_apis = []
        
        if self.lastfm_api_key and self.lastfm_api_key != 'YOUR_LASTFM_API_KEY_HERE':
            available_apis.append('Last.fm')
        else:
            logger.warning("Last.fm API key not configured - mood classification will be limited")
            
        if self.discogs_token and self.discogs_token != 'YOUR_DISCOGS_TOKEN_HERE':
            available_apis.append('Discogs')
        else:
            logger.warning("Discogs token not configured - some genre/year data may be missing")
            
        if self.spotify_client_id and self.spotify_client_secret:
            available_apis.append('Spotify')
            
        available_apis.append('MusicBrainz')  # Always available (no API key needed)
        
        logger.info(f"Available APIs: {', '.join(available_apis)}")
        
    def rate_limit(self):
        """Implement rate limiting for API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def extract_metadata(self, file_path: Path) -> Dict:
        """Extract existing metadata from audio file"""
        try:
            audio = File(str(file_path))
            if audio is None:
                return {}
            
            metadata = {}
            
            # Extract basic metadata
            if hasattr(audio, 'tags'):
                tags = audio.tags
                if hasattr(tags, 'get'):
                    metadata['title'] = tags.get('title', [''])[0] if tags.get('title') else ''
                    metadata['artist'] = tags.get('artist', [''])[0] if tags.get('artist') else ''
                    metadata['album'] = tags.get('album', [''])[0] if tags.get('album') else ''
                    metadata['genre'] = tags.get('genre', [''])[0] if tags.get('genre') else ''
                    metadata['date'] = tags.get('date', [''])[0] if tags.get('date') else ''
                    metadata['mood'] = tags.get('mood', [''])[0] if tags.get('mood') else ''
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {}
    
    def search_musicbrainz(self, artist: str, title: str) -> Dict:
        """Search MusicBrainz for track information"""
        try:
            self.rate_limit()
            
            # Clean search terms
            artist_clean = artist.replace('"', '').strip()
            title_clean = title.replace('"', '').strip()
            
            # Search for recording
            search_query = f'artist:"{artist_clean}" AND recording:"{title_clean}"'
            params = {
                'query': search_query,
                'fmt': 'json',
                'limit': 1
            }
            
            response = self.session.get(f"{self.musicbrainz_url}/recording/", params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('recordings'):
                recording = data['recordings'][0]
                
                result = {
                    'title': recording.get('title', ''),
                    'artist': recording.get('artist-credit', [{}])[0].get('name', ''),
                    'date': recording.get('date', ''),
                    'genre': []
                }
                
                # Get genres from artist
                if recording.get('artist-credit'):
                    artist_id = recording['artist-credit'][0].get('artist', {}).get('id')
                    if artist_id:
                        result['genre'] = self.get_musicbrainz_genres(artist_id)
                
                return result
                
        except Exception as e:
            logger.warning(f"MusicBrainz search failed for {artist} - {title}: {e}")
        
        return {}
    
    def get_musicbrainz_genres(self, artist_id: str) -> List[str]:
        """Get genres for an artist from MusicBrainz"""
        try:
            self.rate_limit()
            
            response = self.session.get(f"{self.musicbrainz_url}/artist/{artist_id}", 
                                      params={'fmt': 'json', 'inc': 'genres'})
            response.raise_for_status()
            
            data = response.json()
            return [genre['name'] for genre in data.get('genres', [])]
            
        except Exception as e:
            logger.warning(f"Failed to get genres for artist {artist_id}: {e}")
            return []
    
    def search_lastfm(self, artist: str, title: str) -> Dict:
        """Search Last.fm for track information and mood tags"""
        if not self.lastfm_api_key or self.lastfm_api_key == 'YOUR_LASTFM_API_KEY_HERE':
            return {}
            
        try:
            self.rate_limit()
            
            params = {
                'method': 'track.getInfo',
                'artist': artist,
                'track': title,
                'api_key': self.lastfm_api_key,
                'format': 'json'
            }
            
            response = self.session.get(self.lastfm_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'track' in data:
                track = data['track']
                
                # Get mood-related tags
                mood_tags = []
                if 'toptags' in track and 'tag' in track['toptags']:
                    mood_tags = [tag['name'] for tag in track['toptags']['tag'][:5]]
                
                return {
                    'genre': track.get('wiki', {}).get('genre', ''),
                    'mood': mood_tags,
                    'year': track.get('wiki', {}).get('published', '')[:4] if track.get('wiki', {}).get('published') else ''
                }
                
        except Exception as e:
            logger.warning(f"Last.fm search failed for {artist} - {title}: {e}")
        
        return {}
    
    def search_discogs(self, artist: str, title: str) -> Dict:
        """Search Discogs for release information"""
        if not self.discogs_token or self.discogs_token == 'YOUR_DISCOGS_TOKEN_HERE':
            return {}
            
        try:
            self.rate_limit()
            
            headers = {
                'Authorization': f'Discogs token={self.discogs_token}'
            }
            
            # Search for release
            params = {
                'q': f'{artist} {title}',
                'type': 'release',
                'limit': 1
            }
            
            response = self.session.get(f"{self.discogs_url}/database/search", 
                                      params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get('results'):
                result = data['results'][0]
                
                # Get detailed release info
                release_id = result['id']
                release_info = self.get_discogs_release(release_id, headers)
                
                return {
                    'year': release_info.get('year', ''),
                    'genre': release_info.get('genres', []),
                    'style': release_info.get('styles', [])
                }
                
        except Exception as e:
            logger.warning(f"Discogs search failed for {artist} - {title}: {e}")
        
        return {}
    
    def get_discogs_release(self, release_id: int, headers: Dict) -> Dict:
        """Get detailed release information from Discogs"""
        try:
            self.rate_limit()
            
            response = self.session.get(f"{self.discogs_url}/releases/{release_id}", 
                                      headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.warning(f"Failed to get Discogs release {release_id}: {e}")
            return {}
    
    def classify_mood(self, tags: List[str], genre: str = '') -> str:
        """Classify mood based on tags and genre"""
        mood_keywords = {
            'energetic': ['energetic', 'upbeat', 'fast', 'dance', 'electronic', 'house', 'techno', 'trance', 'edm'],
            'chill': ['chill', 'ambient', 'relaxed', 'downtempo', 'lounge', 'jazz', 'smooth', 'calm'],
            'emotional': ['emotional', 'melancholic', 'sad', 'romantic', 'ballad', 'deep', 'atmospheric'],
            'aggressive': ['aggressive', 'heavy', 'metal', 'rock', 'hardcore', 'intense', 'powerful'],
            'groovy': ['groovy', 'funk', 'soul', 'disco', 'rhythm', 'swing', 'bass']
        }
        
        # Combine tags and genre for analysis
        text_to_analyze = ' '.join(tags + [genre]).lower()
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                return mood
        
        # Fallback based on genre if no mood keywords found
        genre_lower = genre.lower()
        if any(word in genre_lower for word in ['house', 'techno', 'trance', 'edm', 'dance']):
            return 'energetic'
        elif any(word in genre_lower for word in ['ambient', 'lounge', 'jazz', 'chillout']):
            return 'chill'
        elif any(word in genre_lower for word in ['metal', 'rock', 'hardcore']):
            return 'aggressive'
        elif any(word in genre_lower for word in ['funk', 'soul', 'disco']):
            return 'groovy'
        
        return 'neutral'

    def update_metadata(self, file_path: Path, new_metadata: Dict) -> bool:
        """Update audio file with new metadata"""
        try:
            audio = File(str(file_path))
            if audio is None:
                return False
            
            if hasattr(audio, 'tags'):
                tags = audio.tags
                
                # Update tags
                if new_metadata.get('genre'):
                    tags['genre'] = [new_metadata['genre']]
                
                if new_metadata.get('year'):
                    tags['date'] = [new_metadata['year']]
                
                if new_metadata.get('mood'):
                    tags['mood'] = [new_metadata['mood']]
                
                # Save changes
                audio.save()
                return True
                
        except Exception as e:
            logger.error(f"Error updating metadata for {file_path}: {e}")
        
        return False
    
    def process_file(self, file_path: Path) -> Dict:
        """Process a single audio file"""
        logger.info(f"Processing: {file_path.name}")
        
        # Extract existing metadata
        existing_metadata = self.extract_metadata(file_path)
        
        # Check what's missing
        missing_fields = []
        if not existing_metadata.get('genre'):
            missing_fields.append('genre')
        if not existing_metadata.get('date'):
            missing_fields.append('year')
        if not existing_metadata.get('mood'):
            missing_fields.append('mood')
        
        if not missing_fields:
            logger.info(f"All metadata present for {file_path.name}")
            return {'file': file_path.name, 'status': 'complete', 'updated': False}
        
        # Search for missing information
        artist = existing_metadata.get('artist', '')
        title = existing_metadata.get('title', '')
        
        if not artist or not title:
            logger.warning(f"Missing artist or title for {file_path.name}")
            return {'file': file_path.name, 'status': 'missing_info', 'updated': False}
        
        # Search online databases
        new_metadata = {}
        found_genre = ''
        
        # Try MusicBrainz first
        mb_data = self.search_musicbrainz(artist, title)
        if mb_data:
            if 'genre' in missing_fields and mb_data.get('genre'):
                found_genre = mb_data['genre'][0] if isinstance(mb_data['genre'], list) else mb_data['genre']
                new_metadata['genre'] = found_genre
            if 'year' in missing_fields and mb_data.get('date'):
                new_metadata['year'] = mb_data['date'][:4]
        
        # Try Last.fm for mood and additional info
        lfm_data = self.search_lastfm(artist, title)
        if lfm_data:
            if 'genre' in missing_fields and not new_metadata.get('genre') and lfm_data.get('genre'):
                found_genre = lfm_data['genre']
                new_metadata['genre'] = found_genre
            if 'year' in missing_fields and not new_metadata.get('year') and lfm_data.get('year'):
                new_metadata['year'] = lfm_data['year']
            if 'mood' in missing_fields and lfm_data.get('mood'):
                new_metadata['mood'] = self.classify_mood(lfm_data['mood'], found_genre)
        
        # Try Discogs for additional info
        discogs_data = self.search_discogs(artist, title)
        if discogs_data:
            if 'year' in missing_fields and not new_metadata.get('year') and discogs_data.get('year'):
                new_metadata['year'] = str(discogs_data['year'])
            if 'genre' in missing_fields and not new_metadata.get('genre') and discogs_data.get('genre'):
                found_genre = discogs_data['genre'][0] if discogs_data['genre'] else ''
                new_metadata['genre'] = found_genre
        
        # If we have genre but no mood, try to classify mood from genre
        if 'mood' in missing_fields and not new_metadata.get('mood') and found_genre:
            new_metadata['mood'] = self.classify_mood([], found_genre)
        
        # Update file if we found new metadata
        if new_metadata:
            success = self.update_metadata(file_path, new_metadata)
            if success:
                logger.info(f"Updated {file_path.name} with: {new_metadata}")
                return {'file': file_path.name, 'status': 'updated', 'metadata': new_metadata}
        
        logger.warning(f"Could not find missing metadata for {file_path.name}")
        return {'file': file_path.name, 'status': 'not_found', 'updated': False}
    
    def process_directory(self, directory: Path, max_workers: int = 4):
        """Process all ${FILE_FORMAT} files in a directory"""
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return
        
        # Find all audio files
        audio_files = list(directory.glob(f"**/*.{FILE_FORMAT}"))
        logger.info(f"Found {len(audio_files)} {FILE_FORMAT} files to process")
        
        if not audio_files:
            logger.info(f"No {FILE_FORMAT} files found in directory")
            return
        
        # Process files in parallel
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.process_file, file_path): file_path 
                            for file_path in audio_files}
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    logger.error(f"Error processing {file_path}: {e}")
                    results.append({'file': file_path.name, 'status': 'error', 'error': str(e)})
        
        # Summary
        self.print_summary(results)
    
    def print_summary(self, results: List[Dict]):
        """Print processing summary"""
        total = len(results)
        updated = sum(1 for r in results if r['status'] == 'updated')
        complete = sum(1 for r in results if r['status'] == 'complete')
        errors = sum(1 for r in results if r['status'] == 'error')
        not_found = sum(1 for r in results if r['status'] == 'not_found')
        missing_info = sum(1 for r in results if r['status'] == 'missing_info')
        
        logger.info("\n" + "="*50)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*50)
        logger.info(f"Total files: {total}")
        logger.info(f"Updated: {updated}")
        logger.info(f"Already complete: {complete}")
        logger.info(f"Missing artist/title: {missing_info}")
        logger.info(f"Not found: {not_found}")
        logger.info(f"Errors: {errors}")
        logger.info("="*50)

def load_api_keys(api_keys_path: str) -> Dict:
    """Load API keys from JSON file"""
    try:
        with open(api_keys_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"API keys file not found: {api_keys_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in API keys file: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description="Enrich audio track metadata with online data")
    parser.add_argument("directory", help="Directory containing audio files")
    parser.add_argument("--workers", type=int, default=WORKERS, help="Number of worker threads")
    parser.add_argument("--api-keys", help="Path to JSON file with API keys")
    
    args = parser.parse_args()
    
    # Load API keys if provided
    api_keys = {}
    if args.api_keys:
        api_keys = load_api_keys(args.api_keys)
    else:
        # Try to load from default location
        default_keys_path = Path(API_KEYS_PATH)
        if default_keys_path.exists():
            api_keys = load_api_keys(str(default_keys_path))
    
    directory = Path(args.directory)
    enricher = MetadataEnricher(api_keys)
    enricher.process_directory(directory, args.workers)

if __name__ == "__main__":
    main() 