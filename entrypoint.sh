#!/bin/bash
set -e

# Extract version from language_fixer.py
VERSION=$(grep -oP '__version__\s*=\s*"\K[^"]+' /app/language_fixer.py 2>/dev/null || echo "unknown")

echo "============================================"
echo "🎬 Language-Fixer v${VERSION}"
echo "============================================"
echo "🐳 Container Starting..."
echo ""
echo "🔍 Debug Info:"
echo "   Version: ${VERSION}"
echo "   Python: $(which python3)"
echo "   PATH: $PATH"
echo "   Virtual Env: $VIRTUAL_ENV"
echo ""

# Default IDs if not provided
PUID=${PUID:-568}
PGID=${PGID:-568}
APP_USER=appuser

echo "📋 User Setup:"
echo "   PUID: $PUID"
echo "   PGID: $PGID"

# Check if group exists by GID
if getent group "$PGID" >/dev/null 2>&1; then
    EXISTING_GROUP=$(getent group "$PGID" | cut -d: -f1)
    echo "   ✓ Group $PGID already exists ($EXISTING_GROUP)"
else
    echo "   Creating group with GID $PGID..."
    if groupadd -g "$PGID" "$APP_USER" 2>/dev/null; then
        echo "   ✓ Group created"
    else
        echo "   ⚠ Group creation failed (may already exist)"
    fi
fi

# Check if user exists by UID
if id "$PUID" >/dev/null 2>&1; then
    APP_USER=$(id -un "$PUID")
    echo "   ✓ User $PUID already exists ($APP_USER)"
else
    echo "   Creating user with UID $PUID..."
    if useradd -u "$PUID" -g "$PGID" -M -s /bin/false "$APP_USER" 2>/dev/null; then
        echo "   ✓ User created"
    else
        echo "   ⚠ User creation failed (may already exist)"
        # Try to get the username anyway
        APP_USER=$(id -un "$PUID" 2>/dev/null || echo "appuser")
    fi
fi

echo "   ✅ User setup complete (running as: $APP_USER)"

# Take ownership of necessary paths
echo "📁 Setting permissions..."
if [ -d "/config" ]; then
    echo "   Changing /config ownership to $PUID:$PGID..."
    chown -R "$PUID":"$PGID" /config 2>/dev/null || echo "   Warning: Could not change all /config permissions"
    echo "   ✅ /config ownership set"
else
    echo "   ⚠️ /config directory not mounted"
fi

echo "   ✅ /opt/venv ownership pre-configured (build-time)"
echo ""
echo "============================================"
echo "🚀 Starting application as user $APP_USER ($PUID:$PGID)..."
echo "   Command: python3 /app/language_fixer.py"
echo "============================================"
echo ""

# Execute the main command as the specified user/group with full environment using gosu
exec gosu "$PUID:$PGID" env PATH="/opt/venv/bin:$PATH" VIRTUAL_ENV="/opt/venv" python3 /app/language_fixer.py "$@"
