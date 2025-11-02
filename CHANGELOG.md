# Changelog

All notable changes to language-fixer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# Changelog

## [1.0.12] - 2025-11-02

### Fixed
- **Critical**: Pass through ALL environment variables to sudo command in entrypoint.sh
- Previously only PATH and VIRTUAL_ENV were passed, all config vars were lost
- Now explicitly passes DRY_RUN, SONARR_URL, RADARR_URL, and all other config variables
- This is why DRY_RUN was always True (using default) despite being set to false

## [1.0.11] - 2025-11-02

### Fixed
- **Critical**: Fixed parse_bool() to strip quotes from environment variables
- Added debug output for DRY_RUN parsing to troubleshoot configuration issues
- Should now properly parse DRY_RUN=false even with quotes

## [1.0.10] - 2025-11-02

### Fixed
- **Critical**: Explicitly pass PATH and VIRTUAL_ENV to sudo command
- The -E flag didn't work with sudo -u# syntax
- Now using: sudo -u#UID -g#GID PATH="/opt/venv/bin:$PATH" VIRTUAL_ENV="/opt/venv" python3

## [1.0.9] - 2025-11-02

### Fixed
- **Critical**: Added `-E` flag to sudo to preserve environment variables (PATH, VIRTUAL_ENV)
- Container now properly uses Python venv with requests module available
- Fixed ModuleNotFoundError for requests

## [1.0.8] - 2025-11-02

### Fixed
- **Critical**: Complete revert to v1.0.1 container setup (which worked reliably)
- Back to gosu for user switching (instead of sudo)
- Back to original user/group creation logic
- Removed all "improvements" from v1.0.2-v1.0.7 that caused startup issues

### Changed
- Kept version banner feature from v1.0.3 (the only working improvement)
- All other changes reverted to stable v1.0.1 baseline

**Note**: v1.0.2-v1.0.7 had various startup issues. This version returns to the proven v1.0.1 approach.

## [1.0.7] - 2025-11-02

### Fixed
- **Critical**: Container failed to start due to broken sudoers configuration
- Removed sudoers modification that was breaking sudo
- Root doesn't need sudoers config to switch to other users
- Container now starts reliably

## [1.0.6] - 2025-11-02

### Fixed
- **Critical**: Container startup hang when user/group with PUID/PGID already exists
- Removed user/group creation logic entirely - use numeric UID directly with sudo
- Added sudo NOPASSWD configuration for seamless user switching
- Container now starts immediately without attempting to create users/groups

### Changed
- Simplified user setup to absolute minimum - just verify PUID/PGID and start
- Cleaner logs without unnecessary user creation attempts

## [1.0.5] - 2025-11-02

### Changed
- **Reverted to sudo**: Switched back from gosu to sudo for user switching (more reliable and faster)
- **Simplified user setup**: Removed verbose logging, cleaner output with just essential info
- **Container startup**: No more misleading "Creating group..." messages - silent creation with error suppression

### Fixed
- Container startup logs now show only relevant information
- User/group setup works reliably without verbose status messages

## [1.0.4] - 2025-11-02

### Fixed
- **Container Startup Logs**: Improved group/user existence checks to eliminate misleading "Creating group..." messages when groups already exist
  - Now properly detects existing groups by GID and displays their actual names
  - Clearer output with checkmarks (✓) for existing resources
  - Better error handling with warning symbols (⚠) for edge cases

## [1.0.3] - 2025-01-22

### 🔧 Improved
- **Container Startup Banner**: Added prominent version display at container startup
  - Version is now shown immediately when container starts
  - Dynamically extracted from language_fixer.py (always accurate)
  - Visual separators for better readability
  - Improved startup logging structure
  - Easier to identify which version is running

### 📚 Technical Details
- Version banner appears before all other startup messages
- Uses grep to extract version from Python file
- Consistent formatting with visual separators

---

## [1.0.2] - 2025-11-01

### 🔧 Fixed
- **Container Startup Hanging**: Fixed critical bug where container would hang during user setup
  - Improved user/group detection to handle existing UIDs/GIDs gracefully
  - Added proper error handling for cases where UID 568 already exists
  - Changed gosu to use UID:GID directly instead of username lookup
  - Added more verbose logging for troubleshooting startup issues
  - Fixed permission setting to continue on errors instead of failing

### 🔍 Technical Details
- Root Cause: v1.0.1's gosu implementation didn't handle existing users properly
- Impact: Containers would hang indefinitely at "User Setup" stage
- Solution: Detect existing users and use numeric UID:GID with gosu
- Result: Container startup now completes in ~1.5 minutes as expected

---

## [1.0.1] - 2025-11-01

### 🔧 Fixed
- **LICENSE Consistency**: Removed conflicting MIT-style warranty disclaimer from CC BY-NC-SA 4.0 license file
  - Now contains only CC BY-NC-SA 4.0 compliant disclaimer text
  - Resolves legal ambiguity for commercial use restrictions
- **CI Test Step**: Fixed Docker container test in GitHub Actions workflow
  - Timeout now runs at host level instead of being passed as container argument
  - Added `RUN_INTERVAL_SECONDS=0` to prevent test hanging
  - Test properly validates container startup and basic functionality

### 📚 Improved
- **Documentation Consistency**: Unified DRY_RUN defaults across all examples
  - Docker Compose quick-start now shows `DRY_RUN=true` (safe default)
  - Docker Run quick-start now shows `DRY_RUN=true` (safe default)
  - Added clear 5-step guide for switching to production mode
  - Enhanced safety warnings and review process documentation
- **Missing References**: Removed references to non-existent files
  - Removed `OPTIMIZATION.md` reference from README Contributing section
  - Removed `/scripts/` directory reference from PROJECT_STATUS
- **Security Documentation**: Enhanced .trivyignore with comprehensive metadata
  - Added detailed risk assessments for each ignored CVE
  - Added review dates (2025-11-01) and next review dates
  - Added categorization by vulnerability type and risk level
  - Added justifications for why each CVE is safe to ignore in our context

### ⚡ Changed
- **Container User Switching**: Replaced `sudo` with `gosu` for lightweight process execution
  - Reduced container overhead and improved startup performance
  - More idiomatic for containerized environments
  - Updated Dockerfile to install gosu instead of sudo
- **Code Quality**: Minor code improvements in language_fixer.py
  - Removed duplicate initialization of `MODIFIED_SONARR_PATHS`
  - Removed unused `needs_whisper` variable
  - Added comprehensive docstring for 30-second configuration display timer
  - Improved code clarity and maintainability

### 📖 Documentation Updates
- Updated AGENT_INSTRUCTIONS.md with v1.0.1 improvements and gosu usage
- Updated PROJECT_STATUS.md to reflect v1.0.1 quality improvements
- Enhanced inline code comments for better maintainability

---

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
