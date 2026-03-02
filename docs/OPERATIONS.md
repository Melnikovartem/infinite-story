# Operations Guide - Infinite Story Engine v2

This guide covers deployment, rollback, health checks, and operational procedures for ISE v2.

## Quick Links

- **Deploy:** `backend/scripts/deploy.sh`
- **Rollback:** `backend/scripts/rollback.sh`
- **Health Check:** `backend/scripts/health_check.py`

## Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Code review completed
- [ ] Backup strategy in place
- [ ] Team notified
- [ ] Maintenance window scheduled (if needed)

### Deploy to Staging

```bash
cd backend
./scripts/deploy.sh staging
```

**What it does:**
1. Runs full test suite
2. Installs dependencies
3. Creates data backup
4. Runs any needed migrations
5. Health checks
6. Cleans up old backups (keeps last 5)

**Output:**
```
Deploying ISE v2 to staging...
✓ Running test suite...
✓ All tests passed!
✓ Installing dependencies...
✓ Creating data backup: .infinite_story_data_backup_1640000000
✓ Checking for migrations...
✓ Running health checks...
✅ Deployment to staging successful!
```

### Deploy to Production

```bash
cd backend
./scripts/deploy.sh production
```

**Important:** Production deployments:
- Should be tested on staging first
- Require backup verification
- May need downtime for migrations
- Notify users beforehand

### Custom Version

Deploy specific version:
```bash
./scripts/deploy.sh staging v2.1.0
```

## Rollback Procedures

### Quick Rollback (Most Recent Backup)

```bash
cd backend
./scripts/rollback.sh
```

The script will:
1. Find the most recent backup
2. Ask for confirmation
3. Stop services
4. Create emergency backup
5. Restore from backup
6. Start services
7. Run health checks

### Rollback to Specific Backup

```bash
./scripts/rollback.sh .infinite_story_data_backup_1640000000
```

### Manual Rollback

If scripts fail:

```bash
# 1. Stop services
systemctl stop infinite-story

# 2. Backup current state
mv .infinite_story_data .infinite_story_data_bad

# 3. Restore from backup
cp -r .infinite_story_data_backup_<DATE> .infinite_story_data

# 4. Start services
systemctl start infinite-story

# 5. Verify
python scripts/health_check.py
```

## Health Checks

### Run Health Check

```bash
python scripts/health_check.py
```

**Checks performed:**
- Data directory accessible and writable
- Models can be loaded
- Data can be saved and loaded
- Generator is configured
- Archive system is functional

**Output:**
```
Running health checks...
==================================================
✓ data_access      PASS
✓ model_loading    PASS
✓ data_persistence PASS
✓ generator_setup  PASS
✓ archive_system   PASS
==================================================

Results: 5/5 checks passed
✅ All checks passed - system is healthy
```

### Automated Health Checks

Health checks run automatically during deployment and can be run on a schedule:

```bash
# Cron job for hourly health checks
0 * * * * cd /path/to/backend && python scripts/health_check.py || mail -s "ISE Health Check Failed" admin@example.com
```

## Backup Management

### Backup Location

Backups are stored in the working directory:
```
.infinite_story_data_backup_1640000000/
.infinite_story_data_backup_1639900000/
.infinite_story_data_backup_1639800000/
```

### Backup Retention

- Auto-cleanup keeps last 5 backups
- Manual backups can be archived separately
- Backups are automatic with every deployment

### Manual Backup

```bash
cp -r .infinite_story_data .infinite_story_data_backup_manual_$(date +%Y%m%d_%H%M%S)
```

### Backup Verification

```bash
# List all backups
ls -lah .infinite_story_data_backup_*/

# Check backup integrity
du -sh .infinite_story_data_backup_*/

# Test restore on staging
cp -r .infinite_story_data_backup_<DATE> /tmp/test_restore
cd /tmp/test_restore && python scripts/health_check.py
```

## Monitoring

### System Status

Check if services are running:
```bash
# Using systemctl
systemctl status infinite-story

# Using docker
docker ps | grep infinite-story

# Direct health check
python scripts/health_check.py
```

### Log Files

Monitor application logs:
```bash
# Application logs
tail -f logs/app.log

# System logs
journalctl -u infinite-story -f

# Docker logs
docker logs -f infinite-story
```

### Performance Monitoring

Track key metrics:
```bash
# Data directory size
du -sh .infinite_story_data

# Active processes
ps aux | grep infinite-story

# Memory usage
free -h
```

## Migration Procedures

### Pre-Migration

1. Backup data:
   ```bash
   cp -r .infinite_story_data .infinite_story_data_pre_migration
   ```

2. Test migration on copy:
   ```bash
   cp -r .infinite_story_data .infinite_story_data_test
   cd /tmp && python /path/to/scripts/migrate_v1_to_v2.py --all
   ```

3. Verify results:
   ```bash
   python scripts/health_check.py
   ```

### Run Migration

```bash
cd backend
PYTHONPATH=. python scripts/migrate_v1_to_v2.py --all
```

### Post-Migration

1. Verify data integrity
2. Run health checks
3. Test key features
4. Monitor logs for errors

## Incident Response

### Service Down

```bash
# 1. Check status
systemctl status infinite-story

# 2. Check logs for errors
journalctl -u infinite-story -n 50

# 3. Restart service
systemctl restart infinite-story

# 4. Verify
python scripts/health_check.py
```

### Corrupted Data

```bash
# 1. Stop service
systemctl stop infinite-story

# 2. Restore from backup
./scripts/rollback.sh

# 3. Run health checks
python scripts/health_check.py

# 4. Investigate cause
# Check logs, verify data integrity, etc.
```

### Performance Degradation

```bash
# 1. Check resource usage
free -h
df -h

# 2. Check for hung processes
ps aux | grep infinite-story

# 3. Restart service if needed
systemctl restart infinite-story

# 4. Review application logs
tail -f logs/app.log
```

### API Errors

```bash
# 1. Check service is running
curl http://localhost:8000/health

# 2. Check recent logs
journalctl -u infinite-story -n 100

# 3. Run health checks
python scripts/health_check.py

# 4. Check for database issues
python -c "from app.models import Story; s = Story.load(...)"
```

## Maintenance Windows

### Schedule Downtime

```bash
# Notify users (implement as needed)
echo "Maintenance scheduled: 2024-03-02 02:00-03:00 UTC"

# Wait until window
sleep until_maintenance_time

# Deploy
./scripts/deploy.sh production
```

### During Maintenance

1. Stop accepting new requests
2. Run migrations
3. Deploy updates
4. Run comprehensive health checks
5. Monitor carefully for 30 minutes

### After Maintenance

1. Verify all systems operational
2. Check user-facing features
3. Monitor error logs
4. Send all-clear notification

## Configuration

### Environment Variables

Set in `.env`:
```bash
# API Configuration
OPENROUTER_API_KEY=<your-key>
API_PORT=8000

# Data Storage
DATA_DIR=.infinite_story_data

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### System Configuration

For systemd service:
```ini
[Unit]
Description=Infinite Story Engine
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python -m app.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Install:
```bash
sudo cp infinite-story.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable infinite-story
```

## Troubleshooting

### Deploy Script Fails

**Issue:** Tests fail during deploy

**Solution:**
```bash
# Run tests locally first
pytest tests/ -v

# Fix failures
# Then retry deploy
./scripts/deploy.sh staging
```

**Issue:** Migration fails

**Solution:**
```bash
# Check migration logs
cat migration.log

# Restore backup manually
./scripts/rollback.sh

# Investigate issue
# Fix and retry
```

### Rollback Issues

**Issue:** Rollback script hangs

**Solution:**
```bash
# Cancel the script
Ctrl+C

# Manual rollback
mv .infinite_story_data .infinite_story_data_bad
cp -r .infinite_story_data_backup_<DATE> .infinite_story_data

# Verify
python scripts/health_check.py
```

### Health Check Failures

**Issue:** Data access check fails

**Solution:**
```bash
# Check permissions
ls -la .infinite_story_data

# Fix permissions if needed
chmod 755 .infinite_story_data
chmod 644 .infinite_story_data/*
```

**Issue:** Generator setup fails

**Solution:**
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Set if missing
export OPENROUTER_API_KEY=<your-key>

# Verify in config
python -c "from app.config import settings; print(settings.openrouter_api_key)"
```

## Best Practices

1. **Always backup before deploying** - Deploy script does this automatically
2. **Test on staging first** - Never deploy untested code to production
3. **Monitor after deployment** - Watch logs and metrics for 30 minutes
4. **Keep backups secure** - Store copies off-server
5. **Document changes** - Keep deployment log
6. **Regular health checks** - Automated checks catch issues early
7. **Test rollbacks** - Periodically verify rollback works
8. **Version control** - Track all changes in git

## Deployment Checklist

Before each deployment:

```
[ ] Code review completed
[ ] All tests passing
[ ] Changelog updated
[ ] Version bumped
[ ] Team notified
[ ] Backup strategy verified
[ ] Maintenance window scheduled (if needed)
[ ] Rollback plan documented

During deployment:
[ ] Deploy script runs successfully
[ ] Health checks pass
[ ] No errors in logs
[ ] Key features tested
[ ] Performance acceptable

After deployment:
[ ] Monitor for 30 minutes
[ ] Check error logs
[ ] Verify backups created
[ ] Document deployment
[ ] Team notified of completion
```

---

**For emergency support, check logs first: `journalctl -u infinite-story -n 100`**
