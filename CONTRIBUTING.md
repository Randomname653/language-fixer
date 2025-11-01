# Contributing to Language-Fixer

First off, thank you for considering contributing to Language-Fixer! 🎉

This document provides guidelines and information for contributors. Whether you're reporting bugs, suggesting features, or submitting code changes, this guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Performance Considerations](#performance-considerations)

## 🤝 Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## 🛠️ How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include:

- **Clear title**: Summarize the issue in one sentence
- **Environment details**: Docker version, host OS, container logs
- **Steps to reproduce**: Detailed step-by-step instructions
- **Expected vs actual behavior**: What should happen vs what actually happens
- **Configuration**: Relevant environment variables (sanitize API keys!)
- **Sample files**: If possible, include media file details (not the files themselves)

**Template:**
```markdown
## Bug Report

**Environment:**
- Docker version: 
- Host OS: 
- Image tag: 

**Configuration:**
```yaml
# Your docker-compose.yml environment section (remove API keys!)
```

**Steps to reproduce:**
1. Set up container with config above
2. Place test file in media directory
3. Watch logs for error

**Expected behavior:**
File should be processed successfully

**Actual behavior:**
Processing fails with error: [paste error here]

**Additional context:**
- File type: .mkv
- File size: 2GB
- Audio tracks: 2 (jpn, eng)
- Subtitle tracks: 3 (jpn, eng, ger)
```

### 💡 Suggesting Features

Feature suggestions are welcome! Please include:

- **Use case**: Describe the problem this feature would solve
- **Proposed solution**: How you envision the feature working
- **Alternatives considered**: Other approaches you've thought about
- **Additional context**: Screenshots, examples, or related issues

### 🔧 Code Contributions

We welcome code contributions! Areas where help is especially appreciated:

- **Performance optimizations**: Building on our recent 500-1350x improvements
- **New integrations**: Additional media server APIs (Jellyfin, Emby, etc.)
- **Language detection**: Improvements to AI-powered language identification
- **Error handling**: Better recovery from edge cases
- **Documentation**: Improved guides and examples

## 🏗️ Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- Git

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Randomname653/language-fixer.git
   cd language-fixer
   ```

2. **Create a development branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

3. **Set up test environment:**
   ```bash
   # Copy example configuration
   cp docker-compose.example.yml docker-compose.yml
   
   # Edit configuration for your setup
   # Set DRY_RUN=true for safe testing
   ```

4. **Build and test locally:**
   ```bash
   docker-compose build
   docker-compose up -d
   
   # Watch logs
   docker-compose logs -f
   ```

### Development Workflow

1. **Make changes** to `language_fixer.py` or other files
2. **Test thoroughly** with `DRY_RUN=true` first
3. **Rebuild container** with your changes
4. **Test with real files** (backup important media first!)
5. **Run performance tests** if applicable
6. **Update documentation** as needed

## 📝 Submitting Changes

### Pull Request Process

1. **Update documentation**: Ensure README.md and other docs reflect your changes
2. **Add tests**: Include relevant test cases for new functionality
3. **Performance impact**: Document any performance implications
4. **Version considerations**: Note if this is a breaking change
5. **Create pull request**: Use the template below

### Pull Request Template

```markdown
## Description

Brief description of changes and motivation.

Fixes #(issue number)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)  
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)

## Testing

- [ ] Tested with DRY_RUN=true
- [ ] Tested with real media files
- [ ] Tested integration with Sonarr/Radarr (if applicable)
- [ ] Performance impact measured
- [ ] No regressions in existing functionality

## Configuration Changes

- [ ] No new environment variables
- [ ] New optional environment variables (backwards compatible)
- [ ] New required environment variables (breaking change)
- [ ] Changed default values (potentially breaking)

## Performance Impact

- [ ] No performance impact
- [ ] Performance improvement: [describe]
- [ ] Performance regression: [justify why necessary]

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Changes tested thoroughly
- [ ] No sensitive information in commit history
```

## 🎨 Style Guidelines

### Python Code Style

- **PEP 8 compliance**: Use standard Python formatting
- **Type hints**: Add type hints for new functions when possible
- **Docstrings**: Document complex functions and classes
- **Error handling**: Robust error handling with meaningful messages
- **Logging**: Use appropriate log levels (debug, info, warning, error)

### Code Organization

```python
# Good: Clear function organization
def process_audio_tracks(file_path: str, keep_languages: list) -> bool:
    """
    Process audio tracks in media file.
    
    Args:
        file_path: Path to media file
        keep_languages: List of language codes to preserve
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        # Implementation here
        logger.info(f"Processing audio tracks in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to process audio tracks: {e}")
        return False
```

### Environment Variables

- **Descriptive names**: `KEEP_AUDIO_LANGS` not `AUDIO_LANG`
- **Reasonable defaults**: Provide sensible defaults for optional settings
- **Documentation**: Document all variables in README.md
- **Validation**: Validate environment variables on startup

### Docker Best Practices

- **Multi-stage builds**: Keep images lean
- **Layer optimization**: Minimize layer count
- **Security**: Run as non-root user
- **Health checks**: Include container health checks

## 🧪 Testing

### Manual Testing Checklist

- [ ] **Dry run mode**: Verify no files are modified with `DRY_RUN=true`
- [ ] **Performance**: Test with large files (>5GB) and measure time
- [ ] **Edge cases**: Test with unusual file formats and metadata
- [ ] **Integration**: Test Sonarr/Radarr integration if applicable
- [ ] **Container lifecycle**: Test stop/restart scenarios
- [ ] **Database persistence**: Verify database survives container restarts

### Test Files

Create a variety of test files:

```bash
# Test different scenarios
test_files/
├── large_movie_10gb.mkv          # Performance testing
├── multi_audio_anime.mkv         # Multiple audio tracks
├── subtitle_heavy_film.mkv       # Many subtitle tracks
├── mp4_conversion_test.mp4       # Container conversion
├── unknown_language.mkv          # Whisper API testing
└── edge_case_metadata.mkv        # Unusual metadata
```

### Performance Testing

Use the included performance test script:

```bash
# Run performance comparison
docker exec language-fixer python3 performance_test.py

# Expected output should show significant improvements for metadata operations
```

## ⚡ Performance Considerations

Our recent v2.0 optimizations achieved 500-1350x performance improvements. When contributing:

### Decision Matrix: mkvpropedit vs ffmpeg

```python
# Use mkvpropedit (fast) for:
- Language tag changes
- Audio title updates  
- Default flag modifications
- Metadata-only edits

# Use ffmpeg (full remux) only for:
- Stream removal
- MP4 → MKV conversion
- Adding/removing attachments
- Structural changes
```

### Performance Guidelines

1. **Prefer metadata edits**: Use `mkvpropedit` when possible
2. **Batch operations**: Process multiple changes in single operations
3. **Database efficiency**: Use batch commits, not per-file commits
4. **Memory usage**: Avoid loading entire files into memory
5. **Temporary files**: Clean up temp files promptly

### Measuring Performance

```python
import time
start_time = time.time()

# Your code here

duration = time.time() - start_time
logger.info(f"Operation completed in {duration:.2f} seconds")
```

## 📚 Additional Resources

- **Docker Best Practices**: [Docker documentation](https://docs.docker.com/develop/dev-best-practices/)
- **FFmpeg Reference**: [FFmpeg documentation](https://ffmpeg.org/documentation.html)
- **MKVToolNix**: [MKVToolNix documentation](https://mkvtoolnix.download/doc/)
- **Sonarr API**: [Sonarr API documentation](https://sonarr.tv/docs/api/)
- **Radarr API**: [Radarr API documentation](https://radarr.video/docs/api/)

## 🎯 Current Priorities

Areas where contributions are especially welcome:

1. **Jellyfin/Emby Integration**: Add support for additional media servers
2. **Web UI**: Optional web interface for configuration and monitoring  
3. **Advanced Scheduling**: More flexible scanning schedules
4. **Backup/Restore**: Database backup and restore functionality
5. **Metrics/Monitoring**: Prometheus metrics export
6. **Multi-Architecture**: ARM32 support
7. **Configuration Validation**: Better startup validation and helpful error messages

## ❓ Questions?

- **General questions**: Open a discussion on GitHub
- **Bug reports**: Create an issue with full details
- **Feature requests**: Open an issue with your proposal
- **Security concerns**: Email maintainers directly (don't create public issues)

---

Thank you for contributing to Language-Fixer! 🚀

Your efforts help make media library management easier for everyone.