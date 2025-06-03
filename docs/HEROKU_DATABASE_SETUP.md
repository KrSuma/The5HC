# Heroku PostgreSQL Database Setup Guide

## Quick Setup

```bash
# 1. Add PostgreSQL addon to your Heroku app
heroku addons:create heroku-postgresql:mini

# 2. Verify database is attached
heroku config | grep DATABASE_URL

# 3. Run migrations (automatic with our Procfile)
git push heroku main
```

## Database Plans & Persistence

### Available Plans (All are persistent!)
- **mini** ($5/month): 10K rows, perfect for starting
- **basic** ($9/month): 10M rows
- **standard-0** ($50/month): 64GB storage, follower databases
- **standard-2** ($200/month): 256GB storage, high availability

### Persistence Guarantee
All Heroku PostgreSQL plans provide:
- ✅ **Persistent storage** - Data survives dyno restarts
- ✅ **Automatic backups** - Daily backups retained for 7 days (25 days on Standard plans)
- ✅ **Point-in-time recovery** - Restore to any point in time
- ✅ **High availability** - Automatic failover on Standard plans

## Step-by-Step Configuration

### 1. Create Heroku App (if not done)
```bash
heroku create your-app-name
```

### 2. Add PostgreSQL Database
```bash
# For production use (recommended)
heroku addons:create heroku-postgresql:basic

# For testing/development
heroku addons:create heroku-postgresql:mini
```

### 3. Verify Database Configuration
```bash
# Check DATABASE_URL is set
heroku config

# Get database info
heroku pg:info
```

### 4. Our App Auto-Configuration
Your app already detects Heroku PostgreSQL automatically:
- `src/data/database_config.py` checks for `DATABASE_URL`
- `Procfile` runs migrations on deploy: `release: python src/data/migrate_database.py`
- No manual configuration needed!

## Database Management

### View Database Info
```bash
heroku pg:info
```

### Connect to Database
```bash
# Interactive PostgreSQL shell
heroku pg:psql

# Run SQL query
heroku pg:psql -c "SELECT COUNT(*) FROM clients;"
```

### Backup Management
```bash
# Create manual backup
heroku pg:backups:capture

# List backups
heroku pg:backups

# Download latest backup
heroku pg:backups:download

# Restore from backup
heroku pg:backups:restore b001 DATABASE_URL
```

### Monitor Database
```bash
# View connections and queries
heroku pg:diagnose

# Check database size
heroku pg:info

# View slow queries
heroku pg:outliers
```

## Data Migration from Local

### Export Local SQLite Data
```python
# Run locally to export data
python scripts/export_to_json.py
```

### Import to Heroku PostgreSQL
```bash
# Upload and import
heroku run python scripts/import_from_json.py
```

## Upgrade Database Plan

```bash
# Check current plan
heroku pg:info

# Upgrade to larger plan
heroku addons:upgrade heroku-postgresql:standard-0

# Monitor upgrade progress
heroku pg:wait
```

## Best Practices

### 1. Connection Pooling
Already configured in `database_config.py`:
```python
# Max 20 connections (Heroku limit)
connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)
```

### 2. Regular Backups
```bash
# Schedule weekly manual backups
heroku pg:backups:schedule DATABASE_URL --at "02:00 America/New_York"
```

### 3. Monitor Performance
```bash
# Enable expensive query logging
heroku pg:settings:log-statement all

# View logs
heroku logs --tail --ps postgres
```

### 4. Data Retention
- Keep assessments for compliance
- Archive old sessions periodically
- Use `created_at` timestamps for queries

## Troubleshooting

### Connection Issues
```bash
# Reset database credentials
heroku pg:credentials:rotate

# Restart database
heroku pg:restart
```

### Performance Issues
```bash
# View active connections
heroku pg:ps

# Kill long-running queries
heroku pg:kill PID

# Analyze query performance
heroku pg:diagnose
```

### Storage Issues
```bash
# Check database size
heroku pg:info

# Find large tables
heroku pg:psql -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Common Commands Reference

```bash
# Database info
heroku pg:info
heroku pg:credentials:url

# Backups
heroku pg:backups
heroku pg:backups:capture
heroku pg:backups:download
heroku pg:backups:restore

# Maintenance
heroku pg:maintenance
heroku pg:maintenance:run
heroku pg:reset

# Performance
heroku pg:diagnose
heroku pg:ps
heroku pg:outliers
heroku pg:pull
heroku pg:push
```

## Cost Optimization

1. **Start with mini** ($5/month) for testing
2. **Upgrade to basic** ($9/month) when you have real users
3. **Monitor row count** with `heroku pg:info`
4. **Archive old data** to stay within limits
5. **Use indexes** for better performance

## Your App is Ready!

Your fitness assessment app is already configured for Heroku PostgreSQL:
- ✅ Automatic database detection
- ✅ Migration on deploy
- ✅ Connection pooling
- ✅ Error handling
- ✅ Secure connections

Just add the PostgreSQL addon and deploy! 🚀