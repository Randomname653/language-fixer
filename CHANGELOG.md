# Changelog

All notable changes to language-fixer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-01

### 🚀 Initial Release

### ✨ Core Features
- **Smart Processing Engine**: Automatically chooses between mkvpropedit (fast) vs ffmpeg (full) based on required changes
- **Audio Management**: Language detection, tagging, title standardization, and default track management  
- **Subtitle Management**: Language filtering, default assignment, and cleanup
- **Container Support**: MP4 → MKV conversion and stream management
- **AI Integration**: Whisper API support for automatic language detection of unknown audio tracks

### 🛡️ Data Integrity & Safety
- **Safety-First Defaults**: DRY_RUN=true prevents accidental changes on first run
- **Batch Commit System**: Database commits every 10 files prevent data loss
- **Smart Default Logic**: Remove flags automatically become conservative when DRY_RUN=false
- **30-Second Config Display**: Shows all settings at startup with countdown timer
- **Robust Error Handling**: Retry logic and failure tracking for reliable operation

### 🔄 Integration & Automation
- **Sonarr Integration**: Automatic TV show library scanning and updates
- **Radarr Integration**: Movie library management with rescan notifications
- **Scheduled Processing**: Configurable scan intervals for continuous maintenance
- **Progress Tracking**: SQLite database prevents reprocessing and tracks completion

### ⚡ Performance Optimizations
- **Metadata-Only Operations**: Lightning-fast tag changes using mkvpropedit (2-5 seconds vs 15-45 minutes)
- **Intelligent Remux Logic**: Only performs full remux when structurally necessary
- **Minimal Resource Usage**: Low CPU and memory footprint with zero temporary files for metadata operations
- **Efficient Processing**: Smart decision matrix optimizes speed vs necessity

### 🤖 AI-Powered Features
- **Whisper Integration**: Complete docker-compose stack with GPU/CPU support
- **Automatic Language Detection**: Processes unknown ('und') audio tracks for accurate tagging
- **Batch AI Processing**: Handles large libraries with configurable timeout and retry logic

### � Enterprise-Grade Configuration  
- **Comprehensive Environment Variables**: Fine-grained control over all processing aspects
- **Fallback System**: Safe defaults for all configuration options
- **Debug Tools**: Built-in database analysis and performance testing utilities
- **Professional Documentation**: Complete setup guides and troubleshooting resources
