#!/bin/bash
set -e

echo "🐳 Language-Fixer Container Starting..."
echo "🔍 Debug Info:"
echo "   Python: $(which python3)"
echo "   PATH: $PATH"
echo "   Virtual Env: $VIRTUAL_ENV"

# Default IDs if not provided
PUID=${PUID:-568}
PGID=${PGID:-568}
APP_USER=appuser

echo "📋 User Setup:"
echo "   PUID: $PUID"
echo "   PGID: $PGID"

# Create group and user if they don't exist
if ! getent group "$PGID" > /dev/null; then
    groupadd -g "$PGID" "$APP_USER"
    echo "   ✅ Created group $PGID"
fi
if ! id -u "$APP_USER" > /dev/null 2>&1; then
    useradd -u "$PUID" -g "$PGID" -M -s /bin/false "$APP_USER"
    echo "   ✅ Created user $APP_USER ($PUID)"
fi

# Take ownership of necessary paths
echo "📁 Setting permissions..."
if [ -d "/config" ]; then
    chown -R "$PUID":"$PGID" /config
    echo "   ✅ /config ownership set"
else
    echo "   ⚠️ /config directory not mounted"
fi

# Ensure virtual environment is accessible to the app user
chown -R "$PUID":"$PGID" /opt/venv
echo "   ✅ /opt/venv ownership set"

echo "🚀 Starting application as user $PUID group $PGID..."
echo "   Command: python3 /app/language_fixer.py"

# Execute the main command as the specified user/group with full environment
exec sudo -E -u "$APP_USER" env PATH="/opt/venv/bin:$PATH" VIRTUAL_ENV="/opt/venv" python3 /app/language_fixer.py "$@"
