# 🎬 Language-Fixer

A powerful Docker-based automation tool for managing audio and subtitle language metadata in media libraries. Integrates seamlessly with Sonarr and Radarr to automatically detect, tag, and organize your movie and TV show collections.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/luckyone94/language-fixer)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

## ✨ Features

### 🎵 Audio Management
- **Smart Language Detection**: Uses Whisper API for automatic audio language identification
- **Language Tagging**: Automatically sets correct language metadata (eng, jpn, deu, etc.)
- **Audio Title Formatting**: Standardizes track titles (e.g., "Dolby Digital 2.0 (English)")
- **Default Track Management**: Intelligently sets default audio tracks based on language preferences
- **Commentary Detection**: Preserves director's commentary and special audio tracks

### 📺 Subtitle Management  
- **Language-based Filtering**: Keep only desired subtitle languages
- **Default Track Assignment**: Automatically set preferred subtitle language as default
- **Cleanup**: Remove unwanted subtitle tracks to save space

### 🗂️ Container & Stream Management
- **MP4 → MKV Conversion**: Automatic container conversion for better metadata support
- **Stream Removal**: Remove unwanted audio/subtitle/attachment streams
- **Font Management**: Optional font attachment removal
- **Efficient Processing**: Smart decision between full remux vs metadata-only edits

### 🔄 Integration & Automation
- **Sonarr Integration**: Automatic TV show library scanning and updates
- **Radarr Integration**: Seamless movie library management
- **Scheduled Scanning**: Configurable intervals for library maintenance
- **Progress Tracking**: SQLite database prevents reprocessing of files
- **Batch Processing**: Efficient handling of large libraries

### 🛡️ Reliability & Performance
- **Crash-Safe Database**: Batch commits prevent data loss during interruptions
- **Smart Remux Logic**: Only performs full remux when structurally necessary
- **Metadata-Only Edits**: Uses mkvpropedit for lightning-fast tag changes (500-1350x faster)
- **Error Handling**: Robust retry logic and failure tracking
- **Dry Run Mode**: Test configuration before making changes

## 🚀 Quick Start

### Docker Compose (Recommended)

```yaml
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
      - DRY_RUN=false
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
```

### Docker Run

```bash
docker run -d \\
  --name language-fixer \\
  --restart unless-stopped \\
  -v /path/to/config:/config \\
  -v /path/to/movies:/media/movies \\
  -v /path/to/tv:/media/tv \\
  -e PUID=1000 \\
  -e PGID=1000 \\
  -e DRY_RUN=false \\
  -e KEEP_AUDIO_LANGS=eng,jpn \\
  -e DEFAULT_AUDIO_LANG=eng \\
  luckyone94/language-fixer:latest
```

## ⚙️ Configuration

### 🔧 Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PUID` | 568 | User ID for file permissions |
| `PGID` | 568 | Group ID for file permissions |
| `TZ` | Europe/Berlin | Timezone for logging |
| `DB_PATH` | /config/langfixer.db | SQLite database location |
| `LOG_LEVEL` | info | Logging level (debug, info, warning, error) |
| `RUN_INTERVAL_SECONDS` | 43200 | Scan interval in seconds (12h default) |
| `DRY_RUN` | false | Preview mode - no actual file changes |

### 🎵 Audio Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REMOVE_AUDIO` | true | Remove unwanted audio tracks |
| `RENAME_AUDIO_TRACKS` | true | Standardize audio track titles |
| `KEEP_AUDIO_LANGS` | jpn,deu,eng,und | Audio languages to preserve |
| `DEFAULT_AUDIO_LANG` | jpn | Preferred default audio language |
| `KEEP_COMMENTARY` | true | Preserve commentary tracks |

### 📺 Subtitle Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REMOVE_SUBTITLES` | true | Remove unwanted subtitle tracks |
| `KEEP_SUBTITLE_LANGS` | jpn,deu,eng | Subtitle languages to preserve |
| `DEFAULT_SUBTITLE_LANG` | deu | Preferred default subtitle language |

### 🔗 Integration Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SONARR_URL` | - | Sonarr server URL |
| `SONARR_API_KEY` | - | Sonarr API key |
| `SONARR_PATHS` | /media/tv | Paths monitored by Sonarr |
| `RADARR_URL` | - | Radarr server URL |
| `RADARR_API_KEY` | - | Radarr API key |
| `RADARR_PATHS` | /media/movies | Paths monitored by Radarr |

### 🤖 AI Language Detection

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_API_URL` | - | OpenAI Whisper API endpoint |
| `WHISPER_TIMEOUT` | 300 | Whisper API timeout (seconds) |

### 🔧 Advanced Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FAILURES` | 3 | Skip files after X failures |
| `BATCH_COMMIT_SIZE` | 10 | Database commits every X files |
| `FFMPEG_TIMEOUT` | 1800 | FFmpeg processing timeout (seconds) |
| `MKVPROPEDIT_TIMEOUT` | 300 | mkvpropedit timeout (seconds) |
| `FFMPEG_SAMPLE_TIMEOUT` | 60 | Audio sampling timeout (seconds) |
| `LOG_STATS_ON_COMPLETION` | true | Log detailed statistics after scan |

## 📖 How It Works

### 1. 🔍 File Discovery
- Scans configured paths for `.mkv` and `.mp4` files
- Skips already processed files (tracked in SQLite database)
- Respects failure limits to avoid infinite retry loops

### 2. 🧠 Stream Analysis
- Uses `ffprobe` to analyze video/audio/subtitle streams
- Identifies current language tags and track properties
- Detects commentary tracks and special content

### 3. 🎯 Language Detection
- For untagged audio (`und`): Uses Whisper API if configured
- Samples 3 segments from the file for accurate detection
- Applies majority voting for final language determination

### 4. ⚡ Smart Processing Decision
- **Metadata-Only Changes**: Uses `mkvpropedit` (seconds)
  - Language tag corrections
  - Audio title standardization  
  - Default flag management
- **Full Remux**: Uses `ffmpeg` (minutes) only when necessary
  - Stream removal
  - MP4 → MKV conversion
  - Structural changes

### 5. 💾 Progress Tracking
- Batch commits every 10 files prevent data loss
- Failed files are tracked with retry limits
- Statistics collection for reporting

### 6. 🔄 Integration Updates
- Notifies Sonarr/Radarr of processed files
- Triggers library rescans for updated content
- Maintains sync with media server databases

## 📊 Performance

The recent optimization update delivers massive performance improvements:

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Audio title change (10GB file) | 15-45 min | 2-5 sec | **500-1350x faster** |
| Language tag update | Full remux | mkvpropedit | **99.9% less CPU** |
| Disk I/O | 20GB | <1MB | **99.995% reduction** |
| Memory usage | 10GB temp | 0MB | **100% less temp storage** |

## 🔍 Monitoring & Troubleshooting

### Log Messages to Watch For

```bash
# Successful file skipping (good!)
🚫 Überspringe (Erfolg): movie.mkv

# Batch commits (data safety)
💾 Batch-Commit nach 10 Dateien...

# Processing decisions
⚡ Führe mkvpropedit durch...    # Fast metadata edit
⚙️ Führe Remux (ffmpeg) durch... # Full remux (slower)
```

### Debug Tools

The project includes several debugging utilities:

```bash
# Check database status
docker exec language-fixer python3 debug_database.py

# Analyze performance
docker exec language-fixer python3 performance_test.py

# Troubleshoot commits
docker exec language-fixer python3 batch_commit_fix.py
```

### Common Issues

**Files being reprocessed every run:**
- Check if `/config` volume is persistent
- Verify `DRY_RUN=false`
- Look for database errors in logs

**Long processing times:**
- Disable unnecessary remuxing with `REMOVE_AUDIO=false`
- Use `DRY_RUN=true` to test configuration first
- Check if Whisper API is responding slowly

## 🤝 Contributing

We welcome contributions! Please see [OPTIMIZATION.md](OPTIMIZATION.md) for technical details about recent performance improvements.

### Development Setup

```bash
git clone https://github.com/Randomname653/language-fixer.git
cd language-fixer
# Edit language_fixer.py
# Test with DRY_RUN=true first
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FFmpeg** for media processing capabilities
- **OpenAI Whisper** for AI-powered language detection
- **Sonarr/Radarr** for media library management integration
- **MKVToolNix** for efficient metadata editing

---

**⭐ If this tool helps organize your media library, please consider starring the repository!**