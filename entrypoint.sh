#!/bin/bash
set -e

# Extract version from language_fixer.py
VERSION=$(grep -oP '__version__\s*=\s*"\K[^"]+' /app/language_fixer.py 2>/dev/null || echo "unknown")

echo "============================================"
echo "🎬 Language-Fixer v${VERSION}"
echo "============================================"

# Default IDs if not provided
PUID=${PUID:-568}
PGID=${PGID:-568}
APP_USER=appuser

# Create group and user if they don't exist
if ! getent group "$PGID" > /dev/null; then
    groupadd -g "$PGID" "$APP_USER"
fi
if ! id -u "$APP_USER" > /dev/null 2>&1; then
    useradd -u "$PUID" -g "$PGID" -M -s /bin/false "$APP_USER"
fi

# Take ownership of necessary paths
echo "Setting ownership for /config..."
chown -R "$PUID":"$PGID" /config

echo "Starting application as user $PUID group $PGID..."
# Execute the main command as the specified user/group
# Pass through all environment variables explicitly
exec sudo -u#"$PUID" -g#"$PGID" \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv" \
    DB_PATH="$DB_PATH" \
    LOG_LEVEL="$LOG_LEVEL" \
    RUN_INTERVAL_SECONDS="$RUN_INTERVAL_SECONDS" \
    DRY_RUN="$DRY_RUN" \
    MAX_FAILURES="$MAX_FAILURES" \
    WHISPER_API_URL="$WHISPER_API_URL" \
    WHISPER_TIMEOUT="$WHISPER_TIMEOUT" \
    SONARR_URL="$SONARR_URL" \
    SONARR_API_KEY="$SONARR_API_KEY" \
    SONARR_PATHS="$SONARR_PATHS" \
    RADARR_URL="$RADARR_URL" \
    RADARR_API_KEY="$RADARR_API_KEY" \
    RADARR_PATHS="$RADARR_PATHS" \
    RUN_CLEANUP="$RUN_CLEANUP" \
    REMOVE_AUDIO="$REMOVE_AUDIO" \
    REMOVE_SUBTITLES="$REMOVE_SUBTITLES" \
    REMOVE_ATTACHMENTS="$REMOVE_ATTACHMENTS" \
    RENAME_AUDIO_TRACKS="$RENAME_AUDIO_TRACKS" \
    REMOVE_FONTS="$REMOVE_FONTS" \
    KEEP_COMMENTARY="$KEEP_COMMENTARY" \
    LOG_STATS_ON_COMPLETION="$LOG_STATS_ON_COMPLETION" \
    KEEP_AUDIO_LANGS="$KEEP_AUDIO_LANGS" \
    KEEP_SUBTITLE_LANGS="$KEEP_SUBTITLE_LANGS" \
    DEFAULT_AUDIO_LANG="$DEFAULT_AUDIO_LANG" \
    DEFAULT_SUBTITLE_LANG="$DEFAULT_SUBTITLE_LANG" \
    FFMPEG_TIMEOUT="$FFMPEG_TIMEOUT" \
    MKVPROPEDIT_TIMEOUT="$MKVPROPEDIT_TIMEOUT" \
    FFMPEG_SAMPLE_TIMEOUT="$FFMPEG_SAMPLE_TIMEOUT" \
    BATCH_COMMIT_SIZE="$BATCH_COMMIT_SIZE" \
    python3 /app/language_fixer.py "$@"
