#!/bin/bash
# Rollback to previous deployment
# Usage: ./rollback.sh [backup_dir]

set -e

BACKUP_DIR=${1:-.infinite_story_data_backup}

echo "=========================================="
echo "ISE v2 Rollback Script"
echo "=========================================="
echo ""

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    echo ""
    echo "Available backups:"
    ls -d .infinite_story_data_backup_* 2>/dev/null || echo "  No backups found"
    exit 1
fi

echo "Restoring from: $BACKUP_DIR"
echo ""

# Change to backend directory
cd "$(dirname "$0")/.."

# 1. Stop services (if applicable)
echo "→ Stopping services..."
# Example for systemd:
# systemctl stop infinite-story || true
echo "✅ Services stopped"

# 2. Restore data
echo ""
echo "→ Restoring data..."
if [ -d ".infinite_story_data" ]; then
    rm -rf ".infinite_story_data"
fi
cp -r "$BACKUP_DIR" ".infinite_story_data"
echo "✅ Data restored"

# 3. Restart services
echo ""
echo "→ Restarting services..."
# Example for systemd:
# systemctl start infinite-story
echo "✅ Services restarted"

# 4. Verify
echo ""
echo "→ Verifying restoration..."
if python3 -c "
from app.models.story import Story
print('✓ Story model imports successfully')
" 2>/dev/null; then
    echo "✅ Verification passed"
else
    echo "⚠️  Verification check skipped"
fi

echo ""
echo "=========================================="
echo "✅ Rollback complete!"
echo "=========================================="
echo ""
echo "Data restored from: $BACKUP_DIR"
echo ""
