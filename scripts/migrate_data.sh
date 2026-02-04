#!/bin/bash
# Migrate data from old 6amdev structure to new witmind-data
# Optional - only run if you want to migrate existing projects

set -e

OLD_PATH="${HOME}/6amdev"
NEW_PATH="${HOME}/witmind-data"

echo "[*] Checking for data to migrate..."

if [ ! -d "$OLD_PATH" ]; then
    echo "[!] No old data found at $OLD_PATH"
    exit 0
fi

if [ ! -d "$NEW_PATH" ]; then
    echo "[!] Creating $NEW_PATH..."
    mkdir -p "$NEW_PATH"/{projects/active,logs/queue,cache}
fi

# Check if there are projects to migrate
if [ -d "$OLD_PATH/platform/projects/active" ]; then
    PROJECT_COUNT=$(find "$OLD_PATH/platform/projects/active" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    if [ "$PROJECT_COUNT" -gt 0 ]; then
        echo "[*] Found $PROJECT_COUNT projects to migrate"
        read -p "    Do you want to migrate them? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "[*] Migrating projects..."
            rsync -av --progress "$OLD_PATH/platform/projects/active/" "$NEW_PATH/projects/active/"
            echo "[+] Projects migrated!"
        fi
    fi
fi

# Check if there are logs to migrate
if [ -d "$OLD_PATH/logs" ]; then
    LOG_COUNT=$(find "$OLD_PATH/logs" -type f 2>/dev/null | wc -l)
    if [ "$LOG_COUNT" -gt 0 ]; then
        echo "[*] Found $LOG_COUNT log files"
        read -p "    Do you want to migrate them? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "[*] Migrating logs..."
            rsync -av --progress "$OLD_PATH/logs/" "$NEW_PATH/logs/"
            echo "[+] Logs migrated!"
        fi
    fi
fi

echo ""
echo "[+] Migration complete!"
echo ""
echo "[*] Next steps:"
echo "  1. Update ~/.env: export WITMIND_ROOT=$NEW_PATH"
echo "  2. Restart services: cd ~/witmind/docker && docker compose restart"
echo "  3. Optional: Backup and remove old directory: mv $OLD_PATH $OLD_PATH.backup"
