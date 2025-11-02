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
# Build environment array, only pass variables that are actually set
ENV_VARS=(
    "PATH=/opt/venv/bin:$PATH"
    "VIRTUAL_ENV=/opt/venv"
)

# Add optional environment variables only if they are set and non-empty
[ -n "$DB_PATH" ] && ENV_VARS+=("DB_PATH=$DB_PATH")
[ -n "$LOG_LEVEL" ] && ENV_VARS+=("LOG_LEVEL=$LOG_LEVEL")
[ -n "$RUN_INTERVAL_SECONDS" ] && ENV_VARS+=("RUN_INTERVAL_SECONDS=$RUN_INTERVAL_SECONDS")
[ -n "$DRY_RUN" ] && ENV_VARS+=("DRY_RUN=$DRY_RUN")
[ -n "$MAX_FAILURES" ] && ENV_VARS+=("MAX_FAILURES=$MAX_FAILURES")
[ -n "$WHISPER_API_URL" ] && ENV_VARS+=("WHISPER_API_URL=$WHISPER_API_URL")
[ -n "$WHISPER_TIMEOUT" ] && ENV_VARS+=("WHISPER_TIMEOUT=$WHISPER_TIMEOUT")
[ -n "$SONARR_URL" ] && ENV_VARS+=("SONARR_URL=$SONARR_URL")
[ -n "$SONARR_API_KEY" ] && ENV_VARS+=("SONARR_API_KEY=$SONARR_API_KEY")
[ -n "$SONARR_PATHS" ] && ENV_VARS+=("SONARR_PATHS=$SONARR_PATHS")
[ -n "$RADARR_URL" ] && ENV_VARS+=("RADARR_URL=$RADARR_URL")
[ -n "$RADARR_API_KEY" ] && ENV_VARS+=("RADARR_API_KEY=$RADARR_API_KEY")
[ -n "$RADARR_PATHS" ] && ENV_VARS+=("RADARR_PATHS=$RADARR_PATHS")
[ -n "$RUN_CLEANUP" ] && ENV_VARS+=("RUN_CLEANUP=$RUN_CLEANUP")
[ -n "$REMOVE_AUDIO" ] && ENV_VARS+=("REMOVE_AUDIO=$REMOVE_AUDIO")
[ -n "$REMOVE_SUBTITLES" ] && ENV_VARS+=("REMOVE_SUBTITLES=$REMOVE_SUBTITLES")
[ -n "$REMOVE_ATTACHMENTS" ] && ENV_VARS+=("REMOVE_ATTACHMENTS=$REMOVE_ATTACHMENTS")
[ -n "$RENAME_AUDIO_TRACKS" ] && ENV_VARS+=("RENAME_AUDIO_TRACKS=$RENAME_AUDIO_TRACKS")
[ -n "$REMOVE_FONTS" ] && ENV_VARS+=("REMOVE_FONTS=$REMOVE_FONTS")
[ -n "$KEEP_COMMENTARY" ] && ENV_VARS+=("KEEP_COMMENTARY=$KEEP_COMMENTARY")
[ -n "$LOG_STATS_ON_COMPLETION" ] && ENV_VARS+=("LOG_STATS_ON_COMPLETION=$LOG_STATS_ON_COMPLETION")
[ -n "$KEEP_AUDIO_LANGS" ] && ENV_VARS+=("KEEP_AUDIO_LANGS=$KEEP_AUDIO_LANGS")
[ -n "$KEEP_SUBTITLE_LANGS" ] && ENV_VARS+=("KEEP_SUBTITLE_LANGS=$KEEP_SUBTITLE_LANGS")
[ -n "$DEFAULT_AUDIO_LANG" ] && ENV_VARS+=("DEFAULT_AUDIO_LANG=$DEFAULT_AUDIO_LANG")
[ -n "$DEFAULT_SUBTITLE_LANG" ] && ENV_VARS+=("DEFAULT_SUBTITLE_LANG=$DEFAULT_SUBTITLE_LANG")
[ -n "$FFMPEG_TIMEOUT" ] && ENV_VARS+=("FFMPEG_TIMEOUT=$FFMPEG_TIMEOUT")
[ -n "$MKVPROPEDIT_TIMEOUT" ] && ENV_VARS+=("MKVPROPEDIT_TIMEOUT=$MKVPROPEDIT_TIMEOUT")
[ -n "$FFMPEG_SAMPLE_TIMEOUT" ] && ENV_VARS+=("FFMPEG_SAMPLE_TIMEOUT=$FFMPEG_SAMPLE_TIMEOUT")
[ -n "$BATCH_COMMIT_SIZE" ] && ENV_VARS+=("BATCH_COMMIT_SIZE=$BATCH_COMMIT_SIZE")

# Execute with all environment variables
exec sudo -u#"$PUID" -g#"$PGID" "${ENV_VARS[@]}" python3 /app/language_fixer.py "$@"
