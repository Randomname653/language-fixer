Language-Fixer
Language-Fixer is a powerful, Docker-based automation tool for meticulous media library managers. It integrates seamlessly with Sonarr and Radarr to automatically detect, tag, and organize your movie and TV show collections.
This project was born from frustration. After finding countless tools that almost met the needs of a dedicated media collector, this project was created to do one thing: manage language metadata exactly the way you want, with no compromises.
Features
 * Smart Automation: Integrates with Sonarr and Radarr to scan your library and automatically update media servers after processing.
 * Intelligent Processing: This is the core feature. Language-Fixer analyzes the required changes and decides the most efficient processing method:
   * Metadata-Only Edits: Uses mkvpropedit for lightning-fast changes (2-5 seconds) like correcting language tags, standardizing track titles, or setting default flags.
   * Full Remux: Only uses ffmpeg when structurally necessary (e.g., removing streams, converting MP4 to MKV).
 * AI Language Detection: Optionally integrates with a self-hosted Whisper API to analyze and correctly tag unknown (und) audio tracks.
 * Full Metadata Control:
   * Audio: Sets correct language tags (e.g., eng, jpn), renames tracks to a standard format (e.g., "Dolby Digital 2.0 (English)"), and sets your preferred default language.
   * Subtitles: Removes unwanted languages and sets your preferred default subtitle track.
   * Cleanup: Can remove unwanted streams (audio, subtitle) and attachments (fonts).
   * Preservation: Intelligently identifies and preserves commentary tracks.
 * Stateful & Reliable: Uses an SQLite database to track processed files, preventing re-work and safely managing failures.
Safety First: The Core Philosophy
This tool is built to be safe and conservative, especially when handling large libraries.
 * Dry Run by Default: Language-Fixer always defaults to DRY_RUN=true. It will log exactly what it plans to do (e.g., [DRY_RUN] Would remove subtitle stream 3 (spa)) without touching a single file. You must review the logs and manually set DRY_RUN=false to enable changes.
 * Smart Defaults: When you set DRY_RUN=false, the tool remains conservative. Any destructive setting (like REMOVE_AUDIO or REMOVE_SUBTITLES) that you have not explicitly set will default to false. This prevents accidental deletion of streams.
 * Startup Pause: At startup, the tool displays its full configuration and pauses for 30 seconds, giving you time to review settings and cancel if you spot a mistake.
Quick Start & Installation
Docker Compose (Recommended)
This is the recommended setup for most users.
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
      
      # Optional: Sonarr Integration
      - SONARR_URL=http://your-sonarr:8989
      - SONARR_API_KEY=your-api-key
      - SONARR_PATHS=/media/tv,/media/anime
      
      # Optional: Radarr Integration
      - RADARR_URL=http://your-radarr:7878
      - RADARR_API_KEY=your-api-key
      - RADARR_PATHS=/media/movies
      
      # Optional: Whisper API
      - WHISPER_API_URL=http://your-whisper-server:9000/asr
      - WHISPER_TIMEOUT=300
      
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
 * CPU Fallback: For CPU-only systems, use the onerahmet/openai-whisper-asr-webservice:latest image (no -gpu suffix), set ASR_DEVICE=cpu, use ASR_MODEL=tiny, and remove the entire deploy section.
How It Works
 * File Discovery: Scans configured paths for .mkv and .mp4 files, skipping any already present in the SQLite database.
 * Stream Analysis: Uses ffprobe to analyze all video, audio, and subtitle streams, identifying current language tags, titles, and commentary tracks.
 * Language Detection: If configured, untagged (und) audio tracks are sampled and sent to the Whisper API for identification.
 * Smart Processing Decision: The tool builds a list of required changes and determines if a fast mkvpropedit is sufficient or if a full ffmpeg remux is required.
 * Execution & Tracking: Changes are executed. The file's status (success, failure) is committed to the database in batches to prevent data loss.
 * Notification: If integrated, notifies Sonarr/Radarr of the processed files to trigger a library rescan.
Configuration
Core Settings
| Variable | Default | Description |
|---|---|---|
| PUID | 568 | User ID for file permissions |
| PGID | 568 | Group ID for file permissions |
| TZ | Europe/Berlin | Timezone for logging |
| DB_PATH | /config/langfixer.db | SQLite database location |
| LOG_LEVEL | info | Logging level (debug, info, warning, error) |
| RUN_INTERVAL_SECONDS | 43200 | Scan interval in seconds (12h default) |
| DRY_RUN | true | Safe mode - no file changes. See "Safety First" section. |
Audio Settings
| Variable | Default | Description |
|---|---|---|
| REMOVE_AUDIO | Smart* | Remove unwanted audio tracks |
| RENAME_AUDIO_TRACKS | true | Standardize audio track titles |
| KEEP_AUDIO_LANGS | jpn,deu,eng,und | Audio languages to preserve |
| DEFAULT_AUDIO_LANG | jpn | Preferred default audio language |
| KEEP_COMMENTARY | true | Keep director's commentary |
Subtitle Settings
| Variable | Default | Description |
|---|---|---|
| REMOVE_SUBTITLES | Smart* | Remove unwanted subtitle tracks |
| KEEP_SUBTITLE_LANGS | jpn,deu,eng | Subtitle languages to preserve |
| DEFAULT_SUBTITLE_LANG | deu | Preferred default subtitle language |
* Smart Default: This setting defaults to false when DRY_RUN=false unless explicitly set to true.
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
Performance
The "Smart Processing" engine is key to performance.
| Operation Type | Processing Time | Resource Usage | Use Case |
|---|---|---|---|
| Metadata Changes | 2-5 seconds | <1% CPU, <1MB I/O | Language tags, audio titles, default flags |
| Stream Removal | 5-15 minutes | Moderate CPU | Remove unwanted audio/subtitle tracks |
| Container Conversion | 10-30 minutes | High CPU | MP4 → MKV, structural changes |
 * Zero Waste: No temporary files are created for metadata-only operations.
 * Typical 10GB File: 2-5 seconds for language/title updates.
 * Memory Usage: <100MB footprint.
Monitoring & Troubleshooting
Key Log Messages
Here are common log messages and their meanings (all logs are in English):
# Safety timer at startup
[INFO] Displaying configuration for 30 seconds...

# Successful file processing
[INFO] Successfully processed: movie.mkv
[INFO] Skipping (already processed): movie.mkv

# Processing method indicators
[DEBUG] Performing fast metadata edit (mkvpropedit)...
[INFO] Performing full remux (ffmpeg) as stream removal is required...

# Batch commits for data safety
[DEBUG] Batch committing 10 files to database...

Database Troubleshooting
To check database status and processed files:
docker exec language-fixer python3 debug_database.py

Common Issues
 * Files being reprocessed every run: Ensure your /config volume is persistent and writable by the PUID/PGID. Verify DRY_RUN is false if you expect changes.
 * Slow processing times: Check logs to see if ffmpeg is being used. This is normal if you are removing streams, but if not, your file may require a remux.
 * Container startup issues: Verify PUID/PGID permissions and that your media paths are correctly mounted.
Contributing
Contributions are welcome. Please feel free to submit bug reports, feature requests, or pull requests via GitHub Issues.
License
This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
This software may not be used for commercial purposes.
