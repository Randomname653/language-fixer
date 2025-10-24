#!/bin/bash
set -e

echo "--- Environment variables as root user ---"
printenv | sort
echo "----------------------------------------"

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
# Optional: Set permissions for /app if needed, though usually OK
# chown -R "$PUID":"$PGID" /app

echo "Starting application as user $PUID group $PGID..."
# Execute the main command as the specified user/group, with environment logging
exec sudo -E -u "#$PUID" -g "#$PGID" /bin/bash -c 'echo "--- Environment variables as appuser ---"; printenv | sort; echo "--- End of appuser environment variables ---"; exec python3 /app/language_fixer.py "$@"' bash "$@"
