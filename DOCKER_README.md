# 🎬 Language-Fixer Docker Image

[![Docker Image Size](https://img.shields.io/docker/image-size/luckyone94/language-fixer/latest)](https://hub.docker.com/r/luckyone94/language-fixer)
[![Docker Pulls](https://img.shields.io/docker/pulls/luckyone94/language-fixer)](https://hub.docker.com/r/luckyone94/language-fixer)
[![Docker Stars](https://img.shields.io/docker/stars/luckyone94/language-fixer)](https://hub.docker.com/r/luckyone94/language-fixer)

Powerful Docker automation tool for managing audio and subtitle language metadata in media libraries. Integrates with Sonarr/Radarr and features AI-powered language detection with massive performance optimizations.

## 🚀 Quick Start

```bash
docker run -d \\
  --name language-fixer \\
  --restart unless-stopped \\
  -v /path/to/config:/config \\
  -v /path/to/movies:/media/movies \\
  -v /path/to/tv:/media/tv \\
  -e PUID=1000 \\
  -e PGID=1000 \\
  -e KEEP_AUDIO_LANGS=eng,jpn \\
  -e DEFAULT_AUDIO_LANG=eng \\
  luckyone94/language-fixer:latest
```

## ⚡ Performance Highlights

- **500-1350x faster** than v1.x for metadata operations  
- **Intelligent processing**: Only full remux when necessary
- **Crash-safe**: Batch commits prevent data loss
- **Resource efficient**: 99.9% less CPU/disk usage for common operations

## 🏷️ Available Tags

- `latest` - Latest stable release
- `2.0`, `2.0.x` - Specific version tags
- `main` - Development branch (not recommended for production)

## 🔧 Essential Environment Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `PUID` | 1000 | User ID for file permissions |
| `PGID` | 1000 | Group ID for file permissions |
| `KEEP_AUDIO_LANGS` | eng,jpn,deu | Audio languages to preserve |
| `DEFAULT_AUDIO_LANG` | eng | Preferred default audio |
| `KEEP_SUBTITLE_LANGS` | eng,deu | Subtitle languages to preserve |
| `DRY_RUN` | false | Test mode (no file changes) |

## 📁 Volume Mounts

| Container Path | Description |
|----------------|-------------|
| `/config` | Database and configuration files |
| `/media/movies` | Movie library path |
| `/media/tv` | TV show library path |
| `/media/anime` | Anime library path |

## 🔗 Integration Examples

### With Sonarr
```yaml
environment:
  - SONARR_URL=http://sonarr:8989
  - SONARR_API_KEY=your-api-key
  - SONARR_PATHS=/media/tv,/media/anime
```

### With Radarr
```yaml
environment:
  - RADARR_URL=http://radarr:7878
  - RADARR_API_KEY=your-api-key
  - RADARR_PATHS=/media/movies
```

### With Whisper AI
```yaml
environment:
  - WHISPER_API_URL=http://whisper:9000/asr
  - WHISPER_TIMEOUT=300
```

## 📝 Complete Documentation

For comprehensive setup, configuration options, and troubleshooting:
**[📖 Full Documentation on GitHub](https://github.com/Randomname653/language-fixer)**

## 🏗️ Architecture

- **Base**: Python 3.8+ Alpine Linux
- **Tools**: FFmpeg, MKVToolNix, MediaInfo
- **Database**: SQLite with crash-safe commits
- **APIs**: Sonarr, Radarr, Whisper integration
- **Platforms**: AMD64, ARM64

## 🆕 What's New in v2.0

- **Smart Processing**: Automatic decision between fast metadata edits vs full remux
- **Massive Performance Gains**: 500-1350x faster for common operations  
- **Batch Commits**: Database safety during container stops/restarts
- **Enhanced Logging**: Clear indicators for processing decisions
- **Resource Optimization**: Eliminated unnecessary temporary files

## 💡 Common Use Cases

- **Anime Collections**: Japanese audio with German/English subtitles
- **Multi-Language Libraries**: Standardize metadata across different sources
- **Container Optimization**: Convert MP4 → MKV for better metadata support
- **Automation**: Set-and-forget library maintenance with Sonarr/Radarr
- **Clean Libraries**: Remove unwanted audio/subtitle tracks

## 🐛 Troubleshooting

**Files reprocessing every run?**
```bash
# Check if config volume is persistent
docker exec language-fixer ls -la /config/

# Verify dry run is disabled
docker exec language-fixer env | grep DRY_RUN
```

**Long processing times?**
```bash
# Check processing decisions in logs
docker logs language-fixer | grep "mkvpropedit\\|Remux"

# Test with dry run first
docker exec -e DRY_RUN=true language-fixer python3 language_fixer.py
```

## 📊 Resource Usage

| Operation | CPU | Memory | Disk I/O | Time |
|-----------|-----|--------|----------|------|
| Metadata edit | <1% | <100MB | <1MB | 2-5s |
| Full remux | 100% | 2GB | 20GB | 15-45m |
| Stream removal | 80% | 1GB | 10GB | 5-20m |

*Performance varies by file size and system specifications*

---

⭐ **Star the project on GitHub if this tool helps organize your media library!**

🔗 **Links**: [GitHub](https://github.com/Randomname653/language-fixer) | [Issues](https://github.com/Randomname653/language-fixer/issues) | [Changelog](https://github.com/Randomname653/language-fixer/blob/main/CHANGELOG.md)