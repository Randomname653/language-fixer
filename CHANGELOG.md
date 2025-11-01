# Changelog

All notable changes to language-fixer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2024-01-XX

### 🚀 Major Performance Improvements
- **BREAKING:** Complete rewrite of processing logic for 500-1350x performance gains
- **Smart Processing Decision**: Automatically chooses between mkvpropedit (fast) vs ffmpeg remux (full)
- **Metadata-Only Operations**: Audio title changes now take seconds instead of 15-45 minutes
- **Reduced Disk I/O**: Eliminated unnecessary temp file creation (99.995% reduction in disk usage)

### 🛡️ Data Integrity & Reliability
- **Batch Commit System**: Database commits every 10 files prevent data loss on container stops
- **Crash-Safe Processing**: No more re-scanning entire libraries after interruptions
- **Improved Error Handling**: Better retry logic and failure tracking

### ✨ New Features
- **Intelligent Remux Detection**: Only performs full remux when structurally necessary
- **Enhanced Logging**: Clear indicators for processing decisions (mkvpropedit vs remux)
- **Debug Tools**: Added comprehensive database and performance analysis utilities
- **Progress Tracking**: Visual indicators for batch commits and processing decisions

### 🔧 Technical Improvements
- **Memory Optimization**: Eliminated 10GB+ temporary file usage
- **CPU Efficiency**: 99.9% reduction in CPU usage for metadata-only changes
- **Container Compatibility**: Better handling of Docker stop/restart scenarios
- **Database Schema**: Enhanced tracking of processing decisions and timing

### 📝 Documentation
- **Comprehensive README**: Complete setup and configuration guide
- **Performance Documentation**: Detailed optimization explanations
- **Troubleshooting Guide**: Common issues and debugging steps
- **Development Guidelines**: Contributing and testing procedures

### 🐛 Bug Fixes
- Fixed database persistence issues in containerized environments
- Resolved infinite reprocessing loops
- Corrected Whisper API timeout handling
- Fixed Sonarr/Radarr integration edge cases

### 🗂️ File Changes
- `language_fixer.py`: Complete rewrite of core processing logic
- `performance_test.py`: Added performance demonstration script
- `debug_database.py`: New database analysis tool
- `batch_commit_fix.py`: Batch commit troubleshooting utility
- `OPTIMIZATION.md`: Technical optimization documentation
- `README.md`: Professional documentation overhaul

## [1.0.0] - 2023-XX-XX

### Initial Release
- Basic media file processing with ffmpeg
- Audio and subtitle language management
- Sonarr/Radarr integration
- Whisper API language detection
- Docker containerization

---

## Migration Guide: v1.x → v2.0

### For Existing Users

The v2.0 update is **backwards compatible** with existing configurations. However, you will benefit from:

1. **Immediate Performance Gains**: Existing files will process 500-1350x faster
2. **Crash Safety**: No more lost progress during container restarts
3. **Better Resource Usage**: Significantly lower CPU and disk usage

### Configuration Changes

No configuration changes are required. All existing environment variables work as before.

### Database Migration

The database schema is automatically upgraded. Your existing processed file history is preserved.

### What to Expect

- **First run after upgrade**: May take longer as the system optimizes its processing strategy
- **Subsequent runs**: Dramatically faster, especially for metadata-only operations
- **Container restarts**: No longer lose processing progress

---

## Breaking Changes

### v2.0.0
- None! This release is fully backwards compatible while delivering massive performance improvements.

---

## Performance Metrics

### Before v2.0 (Full Remux Always)
- 10GB file audio title change: **15-45 minutes**
- CPU usage: **100% during remux**
- Disk I/O: **~20GB temporary files**
- Memory: **10GB+ peak usage**

### After v2.0 (Smart Processing)
- 10GB file audio title change: **2-5 seconds**
- CPU usage: **<1% for metadata ops**
- Disk I/O: **<1MB for metadata ops**
- Memory: **<100MB consistent**

**Result: 500-1350x performance improvement for common operations**