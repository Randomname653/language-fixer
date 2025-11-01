---
name: 🐛 Bug Report
about: Create a report to help us improve Language-Fixer
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''

---

## 🐛 Bug Description

A clear and concise description of what the bug is.

## 🌍 Environment

- **Docker Image Tag**: (e.g., `luckyone94/language-fixer:latest`)
- **Host OS**: (e.g., Ubuntu 22.04, Windows 11, macOS 13)
- **Docker Version**: (run `docker --version`)
- **Architecture**: (e.g., x86_64, arm64)

## ⚙️ Configuration

```yaml
# Your docker-compose.yml environment section
# REMOVE API KEYS AND SENSITIVE DATA!
environment:
  - PUID=1000
  - PGID=1000
  - KEEP_AUDIO_LANGS=eng,jpn
  # ... other relevant settings
```

## 📁 Media File Details

- **File Format**: (e.g., MKV, MP4)
- **File Size**: (e.g., 2.5GB)
- **Audio Tracks**: (e.g., 2 tracks: jpn, eng)
- **Subtitle Tracks**: (e.g., 3 tracks: jpn, eng, ger)
- **Duration**: (e.g., 1h 45m)

## 🔄 Steps to Reproduce

1. Start container with configuration above
2. Place test file in `/media/movies/`
3. Wait for processing to begin
4. Observe error in logs

## ✅ Expected Behavior

A clear description of what you expected to happen.

## ❌ Actual Behavior

A clear description of what actually happened.

## 📋 Logs

```
Paste relevant container logs here:
docker logs language-fixer --tail 50

Remove any sensitive information (file paths, API keys, etc.)
```

## 🔍 Additional Context

- Does this happen with all files or specific ones?
- Is this a regression from a previous version?
- Any workarounds you've found?
- Screenshots if applicable

## 🏥 Health Check

- [ ] Container starts successfully
- [ ] Database file is created in `/config/`
- [ ] No permission errors in logs
- [ ] Integration APIs (Sonarr/Radarr) are accessible

## 📊 Performance Impact

- [ ] No performance impact
- [ ] Slower than expected processing
- [ ] High CPU/memory usage
- [ ] Files not completing processing

---

**Note**: For faster resolution, please ensure you've:
- ✅ Searched existing issues for duplicates
- ✅ Tested with `DRY_RUN=true` first
- ✅ Included complete error logs
- ✅ Removed sensitive information