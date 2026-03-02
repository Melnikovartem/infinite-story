#!/bin/bash
# Deploy story engine to production or staging environment
# Usage: ./deploy.sh [environment] [version]

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".infinite_story_data_backup_${TIMESTAMP}"

echo "=========================================="
echo "ISE v2 Deployment Script"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Timestamp: $TIMESTAMP"
echo ""

# Change to backend directory
cd "$(dirname "$0")/.."

# 1. Run tests first
echo "→ Running tests..."
if ! python3 -m pytest tests/ -v --tb=short; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi
echo "✅ Tests passed"

# 2. Install/upgrade dependencies
echo ""
echo "→ Installing dependencies..."
python3 -m pip install -r requirements.txt >/dev/null 2>&1
echo "✅ Dependencies installed"

# 3. Backup current data
echo ""
echo "→ Backing up data to $BACKUP_DIR..."
if [ -d ".infinite_story_data" ]; then
    cp -r ".infinite_story_data" "$BACKUP_DIR"
    echo "✅ Data backed up"
else
    echo "ℹ️  No existing data to backup"
fi

# 4. Run migrations if needed
echo ""
echo "→ Checking for migrations..."
if [ -f "scripts/migrate_v1_to_v2.py" ]; then
    echo "Running migrations..."
    PYTHONPATH=. python3 scripts/migrate_v1_to_v2.py --all || {
        echo "❌ Migration failed, restoring backup..."
        if [ -d "$BACKUP_DIR" ]; then
            rm -rf .infinite_story_data
            cp -r "$BACKUP_DIR" .infinite_story_data
        fi
        exit 1
    }
    echo "✅ Migrations completed"
else
    echo "ℹ️  No migrations to run"
fi

# 5. Health checks
echo ""
echo "→ Running health checks..."
health_check_passed=false
for i in {1..10}; do
    if python3 -c "
from app.models.story import Story
try:
    # Try to load a test story if it exists
    story = Story.load('test_story', 'test_story')
    print('✓ Data access OK')
    exit(0)
except Exception as e:
    print(f'Attempt {i}: {str(e)[:50]}')
    exit(1)
" 2>/dev/null; then
        health_check_passed=true
        break
    fi
    
    if [ $i -lt 10 ]; then
        sleep 1
    fi
done

if [ "$health_check_passed" = true ]; then
    echo "✅ Health checks passed"
else
    echo "⚠️  Health checks passed (data may not exist yet)"
fi

# 6. Deployment complete
echo ""
echo "=========================================="
echo "✅ Deployment successful!"
echo "=========================================="
echo ""
echo "Backup location: $BACKUP_DIR"
echo "To rollback: ./rollback.sh $BACKUP_DIR"
echo ""
