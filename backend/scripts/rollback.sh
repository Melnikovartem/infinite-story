#!/bin/bash
# Rollback Infinite Story Engine to previous deployment
#
# Usage: ./rollback.sh [backup_dir]
#   backup_dir: optional path to backup directory
#              if not provided, uses most recent backup

set -e

BACKUP_DIR=${1:-}

# Find most recent backup if not provided
if [ -z "$BACKUP_DIR" ]; then
    echo "Searching for most recent backup..."
    BACKUP_DIR=$(ls -td .infinite_story_data_backup_* 2>/dev/null | head -1)
    
    if [ -z "$BACKUP_DIR" ]; then
        echo "❌ No backup directories found"
        exit 1
    fi
fi

# Verify backup exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "=========================================="
echo "Rolling back from: $BACKUP_DIR"
echo "=========================================="

# Confirm rollback
read -p "⚠️  Are you sure you want to rollback? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# 1. Stop services
echo "✓ Stopping services..."
if command -v systemctl &> /dev/null; then
    systemctl stop infinite-story || true
fi
if command -v docker &> /dev/null; then
    docker stop infinite-story 2>/dev/null || true
fi
sleep 2

# 2. Create backup of current state before rollback
EMERGENCY_BACKUP=".infinite_story_data_emergency_$(date +%s)"
if [ -d ".infinite_story_data" ]; then
    echo "✓ Creating emergency backup: $EMERGENCY_BACKUP"
    cp -r .infinite_story_data "$EMERGENCY_BACKUP"
fi

# 3. Restore from backup
echo "✓ Restoring data from backup..."
rm -rf .infinite_story_data
cp -r "$BACKUP_DIR" .infinite_story_data
echo "✓ Data restored"

# 4. Start services
echo "✓ Starting services..."
if command -v systemctl &> /dev/null; then
    systemctl start infinite-story || true
fi
if command -v docker &> /dev/null; then
    docker start infinite-story 2>/dev/null || true
fi

# 5. Verify rollback
echo "✓ Verifying rollback..."
sleep 3
attempt=1
max_attempts=10
while [ $attempt -le $max_attempts ]; do
    if PYTHONPATH=. python scripts/health_check.py > /dev/null 2>&1; then
        echo "✓ Health checks passed"
        break
    else
        echo "  Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "⚠️  Health checks failed after rollback"
    echo "⚠️  Emergency backup available at: $EMERGENCY_BACKUP"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Rollback successful!"
echo "✓ Restored from: $BACKUP_DIR"
echo "⚠️  Emergency backup: $EMERGENCY_BACKUP"
echo "=========================================="
exit 0
