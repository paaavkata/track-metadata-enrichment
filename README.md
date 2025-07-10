# Track Metadata Enrichment for DJ Playlists

A Python script to automatically enrich M4A music files with missing metadata (genre, year, mood) by querying online music databases.

## Features

- **Automatic Metadata Detection**: Scans M4A files for existing metadata
- **Multi-Source Enrichment**: Queries MusicBrainz, Last.fm, and Discogs APIs
- **Mood Classification**: Automatically classifies tracks by mood (energetic, chill, emotional, etc.)
- **Parallel Processing**: Processes multiple files simultaneously for efficiency
- **Comprehensive Logging**: Detailed logs of all operations
- **Rate Limiting**: Respects API rate limits to avoid being blocked

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Clone or download this repository
git clone <repository-url>
cd track-metadata-enrichment

# Run the automated setup
python3 setup.py
```

### Option 2: Manual Setup
```bash
# 1. Create a virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test installation
python test_installation.py
```

## API Keys Setup

The script uses several free APIs to enrich your metadata. You'll need to obtain API keys for some services:

### 1. Last.fm API Key (Recommended)
- Go to [Last.fm API](https://www.last.fm/api/account/create)
- Create a free account and generate an API key
- This provides excellent genre and mood information

### 2. Discogs API Token (Recommended)
- Go to [Discogs Developer](https://www.discogs.com/settings/developers)
- Create a free account and generate a token
- Provides detailed release information and genres

### 3. Spotify API (Optional)
- Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Create an app to get Client ID and Secret
- Provides additional audio features for mood classification

### 4. MusicBrainz (No API Key Required)
- Free and open database
- No registration required
- Provides basic genre and release information

## Configuration

1. **Copy the example API keys file**:
   ```bash
   cp api_keys.json.example api_keys.json
   ```

2. **Edit `api_keys.json`** with your actual API keys:
   ```json
   {
       "lastfm_api_key": "your_actual_lastfm_key",
       "discogs_token": "your_actual_discogs_token",
       "spotify_client_id": "your_spotify_client_id",
       "spotify_client_secret": "your_spotify_client_secret"
   }
   ```

## Usage

### Basic Usage
```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Run the script
python track_metadata_enrichment.py /path/to/your/music/directory
```

### Advanced Usage
```bash
# Use 8 worker threads for faster processing
python track_metadata_enrichment.py /path/to/music --workers 8

# Specify custom API keys file
python track_metadata_enrichment.py /path/to/music --api-keys /path/to/api_keys.json
```

### Example Output
```
2024-01-15 10:30:15 - INFO - Found 150 M4A files to process
2024-01-15 10:30:16 - INFO - Processing: track1.m4a
2024-01-15 10:30:18 - INFO - Updated track1.m4a with: {'genre': 'House', 'year': '2020', 'mood': 'energetic'}
2024-01-15 10:30:19 - INFO - Processing: track2.m4a
2024-01-15 10:30:21 - INFO - All metadata present for track2.m4a

==================================================
PROCESSING SUMMARY
==================================================
Total files: 150
Updated: 45
Already complete: 95
Missing artist/title: 2
Not found: 8
Errors: 0
==================================================
```

## How It Works

### 1. Metadata Extraction
- Reads existing metadata from M4A files using the `mutagen` library
- Identifies missing fields (genre, year, mood)

### 2. Online Search Strategy
The script searches multiple databases in order of reliability:

1. **MusicBrainz** (free, no API key required)
   - Basic genre and release year information
   - Artist-based genre classification

2. **Last.fm** (requires API key)
   - Detailed genre information
   - User-generated mood tags
   - Track popularity data

3. **Discogs** (requires API token)
   - Release year and detailed genre information
   - Style classifications
   - Album context

### 3. Mood Classification
The script automatically classifies tracks into mood categories:
- **Energetic**: Fast, upbeat, dance, electronic
- **Chill**: Ambient, relaxed, downtempo, lounge
- **Emotional**: Melancholic, romantic, ballad
- **Aggressive**: Heavy, metal, rock, hardcore
- **Groovy**: Funk, soul, disco, rhythm
- **Neutral**: Default when no mood indicators found

### 4. Metadata Update
- Updates M4A files with new metadata tags
- Preserves existing metadata
- Handles errors gracefully

## File Structure

```
track-metadata-enrichment/
├── track_metadata_enrichment.py    # Main script
├── requirements.txt                # Python dependencies
├── api_keys.json.example          # Example API configuration
├── api_keys.json                  # Your API keys (create this)
├── setup.py                       # Automated setup script
├── test_installation.py           # Installation test script
├── metadata_enrichment.log        # Processing logs (auto-generated)
├── venv/                          # Virtual environment (created during setup)
└── README.md                      # This file
```

## Supported Metadata Fields

The script enriches these metadata fields:

| Field | Description | Source |
|-------|-------------|---------|
| `genre` | Musical genre | MusicBrainz, Last.fm, Discogs |
| `date` | Release year | MusicBrainz, Last.fm, Discogs |
| `mood` | Track mood/energy | Last.fm tags, classification |

## Troubleshooting

### Common Issues

1. **"No M4A files found"**
   - Ensure your directory contains `.m4a` files
   - Check file permissions

2. **"API key errors"**
   - Verify your API keys are correct
   - Check if you've exceeded API rate limits
   - Ensure your API keys have the necessary permissions

3. **"Permission denied" errors**
   - Make sure you have write permissions to the music directory
   - Try running with appropriate user permissions

4. **"No metadata found" for tracks**
   - Some obscure tracks may not be in the databases
   - Try searching with different artist/title variations
   - Check if the track has sufficient existing metadata

5. **"externally-managed-environment" error**
   - Use the virtual environment setup as described above
   - Don't install packages globally on modern Python systems

### Rate Limiting

The script includes built-in rate limiting to respect API limits:
- 1 second between requests (configurable)
- Automatic retry logic for failed requests
- Graceful handling of API errors

## Performance Tips

1. **Use multiple workers** for large collections:
   ```bash
   python track_metadata_enrichment.py /path/to/music --workers 8
   ```

2. **Process in batches** if you have thousands of files:
   - Split your music into subdirectories
   - Process each subdirectory separately

3. **Monitor the log file** for progress:
   ```bash
   tail -f metadata_enrichment.log
   ```

## Contributing

Feel free to contribute improvements:
- Add support for additional music databases
- Improve mood classification algorithms
- Add support for other audio formats
- Enhance error handling and recovery

## License

This project is open source. Feel free to use and modify for your needs.

## Disclaimer

- Always backup your music files before running the script
- The script modifies your original files
- API usage is subject to the terms of service of each provider
- Some tracks may not be found in the databases 