Language-Fixer
A powerful Docker-based automation tool for managing audio and subtitle language metadata in media libraries. It integrates with Sonarr and Radarr to automatically detect, tag, and organize your movie and TV show collections.
Features
Language-Fixer provides a comprehensive set of features for media library management:
 * Integration: Seamlessly connects with Sonarr and Radarr for library scanning and updates.
 * AI Language Detection: Optionally uses a self-hosted Whisper API to identify and tag unknown (und) audio tracks.
 * Audio Management:
   * Sets correct language metadata (e.g., eng, jpn, deu).
   * Standardizes track titles (e.g., "Dolby Digital 2.0 (English)").
   * Intelligently sets default audio tracks based on user preferences.
   * Preserves director's commentary and special audio tracks.
 * Subtitle Management:
   * Filters and keeps only desired subtitle languages.
   * Assigns a preferred subtitle language as the default.
   * Removes unwanted subtitle tracks to save space.
 * Container and Stream Management:
   * Automatically converts .mp4 files to .mkv for better metadata support.
   * Removes unwanted audio, subtitle, or attachment streams (e.g., fonts).
 * Performance and Reliability:
   * Smart Processing: Uses mkvpropedit for metadata-only edits (500-1350x faster) and only performs a full ffmpeg remux when structurally necessary.
   * Stateful Processing: An SQLite database prevents reprocessing of files and tracks failures.
   * Safety: DRY_RUN=true is the default to allow reviewing planned changes before execution. Batch commits prevent data loss during interruptions.
Quick Start
> Safety First: Language-Fixer defaults to DRY_RUN=true.
>  * Run the container with DRY_RUN=true (default).
>  * Review the container logs (docker logs language-fixer) to verify planned changes.
>  * Set DRY_RUN=false in your configuration only after confirming the changes are correct.
>  * The tool's smart defaults automatically become conservative (e.g., REMOVE_AUDIO=false) when DRY_RUN is disabled.
> 
> Automatic Updates:
> Using the :latest tag ensures Language-Fixer checks for new versions at startup.
> Update your stack with: docker compose pull && docker compose up -d
> 
Docker Compose (Recommended)
version: '3.8'

services:
  language-fixer:
    image: luckyone94/language-fixer:latest
    container_name: language-fixer
    restart: unless-stopped
    environment:
      # User Configuration
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Berlin
      
      # Database & Logging
      - DB_PATH=/config/langfixer.db
      - LOG_LEVEL=info
      
      # Schedule & Behavior
      - RUN_INTERVAL_SECONDS=43200  # 12 hours
      - DRY_RUN=true                # SAFE DEFAULT: Review changes first!
      - RUN_CLEANUP=true
      
      # Audio Configuration
      - REMOVE_AUDIO=true
      - RENAME_AUDIO_TRACKS=true
      - KEEP_AUDIO_LANGS=jpn,deu,eng,und
      - DEFAULT_AUDIO_LANG=jpn
      
      # Subtitle Configuration  
      - REMOVE_SUBTITLES=true
      - KEEP_SUBTITLE_LANGS=jpn,deu,eng
      - DEFAULT_SUBTITLE_LANG=deu
      
      # Optional: Whisper API for unknown language detection
      - WHISPER_API_URL=http://your-whisper-server:9000/asr
      - WHISPER_TIMEOUT=300
      
      # Optional: Sonarr Integration
      - SONARR_URL=http://your-sonarr:8989
      - SONARR_API_KEY=your-api-key
      - SONARR_PATHS=/media/tv,/media/anime
      
      # Optional: Radarr Integration
      - RADARR_URL=http://your-radarr:7878
      - RADARR_API_KEY=your-api-key
      - RADARR_PATHS=/media/movies
      
      # Advanced Options
      - REMOVE_ATTACHMENTS=false
      - REMOVE_FONTS=false
      - KEEP_COMMENTARY=true
      - MAX_FAILURES=3
      
    volumes:
      - /path/to/config:/config
      - /path/to/movies:/media/movies
      - /path/to/tv:/media/tv
      - /path/to/anime:/media/anime

Docker Run
docker run -d \
  --name language-fixer \
  --restart unless-stopped \
  -v /path/to/config:/config \
  -v /path/to/movies:/media/movies \
  -v /path/to/tv:/media/tv \
  -e PUID=1000 \
  -e PGID=1000 \
  -e DRY_RUN=true \
  -e KEEP_AUDIO_LANGS=eng,jpn \
  -e DEFAULT_AUDIO_LANG=eng \
  luckyone94/language-fixer:latest

Complete Stack with AI Language Detection
For automatic language detection of und audio tracks, run a local Whisper ASR service alongside Language-Fixer.
version: '3.8'

services:
  # AI-Powered Language Detection Service
  openai-whisper-asr-webservice:
    image: onerahmet/openai-whisper-asr-webservice:latest-gpu
    container_name: whisper-asr
    restart: unless-stopped
    ports:
      - '9000:9000'
    environment:
      - ASR_ENGINE=faster_whisper
      - ASR_MODEL=small           # Options: tiny, small, medium, large
      - ASR_DEVICE=cuda           # Use 'cpu' if no GPU available
      - FASTER_WHISPER_COMPUTE_TYPE=float16
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
              count: 1
              driver: nvidia
    # For CPU-only systems, remove the deploy section and set ASR_DEVICE=cpu

  # Main Language-Fixer Service
  language-fixer:
    image: luckyone94/language-fixer:latest
    container_name: language-fixer
    restart: unless-stopped
    depends_on:
      - openai-whisper-asr-webservice
    environment:
      # User Configuration
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Berlin
      
      # Core Settings
      - DRY_RUN=true
      - KEEP_AUDIO_LANGS=jpn,deu,eng,und
      - DEFAULT_AUDIO_LANG=jpn
      - KEEP_SUBTITLE_LANGS=jpn,deu,eng
      - DEFAULT_SUBTITLE_LANG=deu
      
      # AI Language Detection Integration
      - WHISPER_API_URL=http://openai-whisper-asr-webservice:9000/asr
      - WHISPER_TIMEOUT=300
      
    volumes:
      - /path/to/config:/config
      - /path/to/movies:/media/movies
      - /path/to/tv:/media/tv

networks:
  default:
    name: media-stack

Whisper Service Details:
 * GPU Support: NVIDIA GPU recommended.
 * CPU Fallback: Remove the deploy section and set ASR_DEVICE=cpu.
 * Model Options: tiny (~1GB VRAM), small (~2GB VRAM) [Recommended], medium (~5GB VRAM), large (~10GB VRAM).
CPU-Only Alternative
For CPU-only systems, use the following configuration for the Whisper service:
  openai-whisper-asr-webservice:
    image: onerahmet/openai-whisper-asr-webservice:latest  # Note: no '-gpu' suffix
    container_name: whisper-asr
    restart: unless-stopped
    ports:
      - '9000:9000'
    environment:
      - ASR_ENGINE=faster_whisper
      - ASR_MODEL=tiny            # 'tiny' is recommended for CPU
      - ASR_DEVICE=cpu
    # Remove the entire 'deploy' section

Configuration
> Startup Display: Language-Fixer shows a detailed configuration summary for 30 seconds at startup, displaying all active settings, defaults used, and safety warnings.
> 
Core Settings
| Variable | Default | Description |
|---|---|---|
| PUID | 568 | User ID for file permissions |
| PGID | 568 | Group ID for file permissions |
| TZ | Europe/Berlin | Timezone for logging |
| DB_PATH | /config/langfixer.db | SQLite database location |
| LOG_LEVEL | info | Logging level (debug, info, warning, error) |
| RUN_INTERVAL_SECONDS | 43200 | Scan interval in seconds (12h default) |
| DRY_RUN | true | Safe mode - no file changes |
Audio Settings
| Variable | Default | Description |
|---|---|---|
| REMOVE_AUDIO | Smart* | Remove unwanted audio tracks |
| RENAME_AUDIO_TRACKS | true | Standardize audio track titles |
| KEEP_AUDIO_LANGS | jpn,deu,eng,und | Audio languages to preserve |
| DEFAULT_AUDIO_LANG | jpn | Preferred default audio language |
| KEEP_COMMENTARY | true | Keep director's commentary |
*Smart Default: true when DRY_RUN=true, false when DRY_RUN=false (safety!)
Subtitle Settings
| Variable | Default | Description |
|---|---|---|
| REMOVE_SUBTITLES | Smart* | Remove unwanted subtitle tracks |
| KEEP_SUBTITLE_LANGS | jpn,deu,eng | Subtitle languages to preserve |
| DEFAULT_SUBTITLE_LANG | deu | Preferred default subtitle language |
*Smart Default: true when DRY_RUN=true, false when DRY_RUN=false (safety!)
Integration Settings
| Variable | Default | Description |
|---|---|---|
| SONARR_URL | - | Sonarr server URL |
| SONARR_API_KEY | - | Sonarr API key |
| SONARR_PATHS | /media/tv | Paths monitored by Sonarr |
| RADARR_URL | - | Radarr server URL |
| RADARR_API_KEY | - | Radarr API key |
| RADARR_PATHS | /media/movies | Paths monitored by Radarr |
AI Language Detection
| Variable | Default | Description |
|---|---|---|
| WHISPER_API_URL | - | OpenAI Whisper API endpoint |
| WHISPER_TIMEOUT | 300 | Whisper API timeout (seconds) |
Advanced Options
| Variable | Default | Description |
|---|---|---|
| MAX_FAILURES | 3 | Skip files after X failures |
| BATCH_COMMIT_SIZE | 10 | Database commits every X files |
| FFMPEG_TIMEOUT | 1800 | FFmpeg processing timeout (seconds) |
| MKVPROPEDIT_TIMEOUT | 300 | mkvpropedit timeout (seconds) |
| FFMPEG_SAMPLE_TIMEOUT | 60 | Audio sampling timeout (seconds) |
| LOG_STATS_ON_COMPLETION | true | Log detailed statistics after scan |
How It Works
 * File Discovery: Scans configured paths for .mkv and .mp4 files, skipping already processed files based on the SQLite database.
 * Stream Analysis: Uses ffprobe to analyze all streams, identifying language tags, titles, and commentary tracks.
 * Language Detection: If configured, untagged (und) audio tracks are sampled and analyzed by the Whisper API to determine the correct language.
 * Smart Processing Decision: The tool decides whether to use fast mkvpropedit (for metadata-only changes) or a full ffmpeg remux (for stream removal or container conversion).
 * Progress Tracking: Changes are committed to the database in batches to prevent data loss.
 * Integration Updates: Notifies Sonarr/Radarr of processed files to trigger library rescans.
Performance
Smart Processing Engine
| Operation Type | Processing Time | Resource Usage | Use Case |
|---|---|---|---|
| Metadata Changes | 2-5 seconds | <1% CPU, <1MB I/O | Language tags, audio titles, default flags |
| Stream Removal | 5-15 minutes | Moderate CPU | Remove unwanted audio/subtitle tracks |
| Container Conversion | 10-30 minutes | High CPU | MP4 → MKV, structural changes |
Processing Logic
 * mkvpropedit: Used for metadata-only changes (most operations).
 * ffmpeg remux: Used only when structural changes are required.
 * Zero Waste: No temporary files are created for metadata operations.
Typical Performance
 * 10GB Movie File: 2-5 seconds for language/title updates.
 * Memory Usage: <100MB footprint.
Monitoring & Troubleshooting
Key Log Messages
# Safety timer at startup
Zeige Konfiguration für 30 Sekunden...

# Successful file processing
Erfolgreich verarbeitet: movie.mkv
Überspringe (bereits verarbeitet): movie.mkv

# Processing method indicators
Führe mkvpropedit durch...    # Fast metadata edit
Führe Remux (ffmpeg) durch... # Full remux required

# Batch commits for data safety
Batch-Commit nach 10 Dateien...

Database Troubleshooting
Check database status and processed files:
docker exec language-fixer python3 debug_database.py

Common Issues
 * Files being reprocessed every run: Ensure /config volume is persistent and writable. Verify DRY_RUN=false.
 * Slow processing times: Check logs to see if ffmpeg is being used instead of mkvpropedit. Check Whisper API responsiveness.
 * Container startup issues: Verify PUID/PGID permissions and that media paths are correctly mounted.
Contributing
Contributions are welcome. Please submit bug reports, feature requests, or pull requests via GitHub.
Development Setup
git clone https://github.com/Randomname653/language-fixer.git
cd language-fixer
# Edit language_fixer.py
# Test with DRY_RUN=true first

License
This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
Non-Commercial Use Only: This software may not be used for commercial purposes.
Acknowledgments
 * FFmpeg
 * OpenAI Whisper
 * Sonarr & Radarr
 * MKVToolNix
