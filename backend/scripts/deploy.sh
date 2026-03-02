#!/bin/bash
# Deploy Infinite Story Engine v2 to production/staging
#
# Usage: ./deploy.sh [environment] [version]
#   environment: staging (default) or production
#   version: latest (default) or specific version tag

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
BACKUP_DATE=$(date +%s)
BACKUP_DIR=".infinite_story_data_backup_${BACKUP_DATE}"

echo "=========================================="
echo "Deploying ISE v2 to $ENVIRONMENT"
echo "Version: $VERSION"
echo "=========================================="

# 1. Verify environment
echo "✓ Verifying environment..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Run from backend directory."
    exit 1
fi

# 2. Run tests first
echo "✓ Running test suite..."
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if ! pytest tests/ -v --tb=short; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi
echo "✓ All tests passed!"

# 3. Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}
echo "✓ Dependencies installed"

# 4. Backup current data
echo "✓ Creating data backup: $BACKUP_DIR"
if [ -d ".infinite_story_data" ]; then
    cp -r .infinite_story_data "$BACKUP_DIR"
    echo "✓ Backup created successfully"
else
    echo "⚠ No existing data to backup"
fi

# 5. Run migrations if needed
echo "✓ Checking for migrations..."
if [ -f "scripts/migrate_v1_to_v2.py" ]; then
    echo "✓ Running migrations..."
    PYTHONPATH=. python scripts/migrate_v1_to_v2.py --all 2>&1 | tee migration.log || {
        echo "❌ Migration failed. Restoring backup..."
        if [ -d "$BACKUP_DIR" ]; then
            rm -rf .infinite_story_data
            cp -r "$BACKUP_DIR" .infinite_story_data
        fi
        exit 1
    }
    echo "✓ Migrations completed successfully"
else
    echo "⚠ No migrations to run"
fi

# 6. Verify installation
echo "✓ Verifying installation..."
PYTHONPATH=. python -c "import app; print('✓ Installation verified')" || {
    echo "❌ Installation verification failed"
    exit 1
}

# 7. Health checks
echo "✓ Running health checks..."
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
    echo "❌ Health checks failed after $max_attempts attempts"
    if [ -d "$BACKUP_DIR" ]; then
        echo "⚠ Rolling back..."
        rm -rf .infinite_story_data
        cp -r "$BACKUP_DIR" .infinite_story_data
    fi
    exit 1
fi

# 8. Cleanup old backups (keep last 5)
echo "✓ Cleaning up old backups..."
ls -td .infinite_story_data_backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ Deployment to $ENVIRONMENT successful!"
echo "✅ Backup location: $BACKUP_DIR"
echo "=========================================="
exit 0
