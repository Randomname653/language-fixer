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
# Execute the main command as the specified user/group with environment preserved
exec sudo -E -u#"$PUID" -g#"$PGID" python3 /app/language_fixer.py "$@"
