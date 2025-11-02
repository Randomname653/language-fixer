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
echo "   ✅ Ready"
echo ""

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
echo "🚀 Starting application as UID:GID $PUID:$PGID..."
echo "   Command: python3 /app/language_fixer.py"
echo "============================================"
echo ""

# Execute the main command as the specified user using sudo with numeric UID
exec sudo -E -u "#$PUID" python3 /app/language_fixer.py "$@"
