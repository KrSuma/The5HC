# The5HC Deployment Guide

**Status**: ✅ READY FOR DEPLOYMENT 🚀  
**Last Updated**: 2025-06-09  
**Platform**: Heroku with PostgreSQL

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment Readiness Checklist](#deployment-readiness-checklist)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Scaling & Production](#scaling--production)

## Prerequisites

### Required Tools
- Git installed and configured
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
- Heroku account (free tier is sufficient to start)
- Python 3.11.10 or higher

### Important Files for Deployment
- ✅ `Procfile` - Tells Heroku how to run the app
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version specification
- ✅ `config/config_production.py` - Production settings
- ✅ `.gitignore` - Prevents sensitive files from being deployed

## Deployment Readiness Checklist

### ✅ Code Readiness
- [x] Database compatibility layer for PostgreSQL
- [x] Environment-based configuration
- [x] Error handling and logging
- [x] Session management and authentication
- [x] All core features working

### ✅ Database Readiness
- [x] Migration scripts support PostgreSQL
- [x] Connection string parsing (`dj-database-url`)
- [x] Automatic table creation on deployment
- [x] Data export/import scripts available

### ✅ Configuration
- [x] Production settings separated
- [x] Secret key management via environment
- [x] Debug mode disabled for production
- [x] Static file serving configured

### ✅ Dependencies
- [x] All requirements in `requirements.txt`
- [x] Production-only dependencies included
- [x] Version numbers specified
- [x] Python version in `runtime.txt`

### ✅ Testing
- [x] All tests passing
- [x] PostgreSQL compatibility tested
- [x] Deployment script tested locally

## Step-by-Step Deployment

### 1. Create Heroku App
```bash
heroku create the5hc-fitness
# Or use your preferred app name
```

### 2. Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:mini
# This creates a free PostgreSQL database
```

### 3. Set Environment Variables
```bash
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
heroku config:set DEBUG=False
heroku config:set LOG_LEVEL=INFO
```

### 4. Deploy to Heroku
```bash
git add .
git commit -m "Deploy The5HC to Heroku"
git push heroku main
```

### 5. Run Database Migration
```bash
heroku run python src/data/migrate_database.py
```

### 6. Create Admin User
```bash
heroku run python -c "
from src.services.auth_service import AuthService
AuthService.create_trainer('admin', 'admin@the5hc.com', 'your-secure-password')
"
```

### 7. Open Your App
```bash
heroku open
```

## Environment Configuration

### Production Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection (auto-set by Heroku) | postgres://... |
| `SECRET_KEY` | Django secret key | Random 32+ char string |
| `DEBUG` | Debug mode | False |
| `LOG_LEVEL` | Logging verbosity | INFO |

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Database | SQLite | PostgreSQL |
| Debug Mode | True | False |
| Secret Key | Default | Environment Variable |
| Static Files | Streamlit serves | WhiteNoise serves |
| Error Pages | Detailed | User-friendly |
| Logging | Console | Heroku logs |

## Database Setup

### Automatic Migration
The application automatically detects the database type and runs appropriate migrations:

```python
# In src/data/database_config.py
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # PostgreSQL for production
else:
    # SQLite for development
```

### Data Migration
To migrate existing data from development to production:

```bash
# Export from local SQLite
python scripts/export_to_json.py

# Import to Heroku PostgreSQL
heroku run python scripts/import_from_json.py
```

## Post-Deployment

### Monitor Logs
```bash
heroku logs --tail
```

### Check Application Status
```bash
heroku ps
```

### Database Backups
```bash
# Create manual backup
heroku pg:backups:capture

# Schedule automatic backups (requires paid plan)
heroku pg:backups:schedule DATABASE_URL --at '02:00 Asia/Seoul'
```

### Performance Monitoring
```bash
# View metrics
heroku metrics

# Check database performance
heroku pg:diagnose
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Error (H10)
```bash
heroku logs --tail
# Check for missing dependencies or startup errors
```

#### 2. Database Connection Error
```bash
heroku config
# Verify DATABASE_URL is set
heroku pg:info
# Check database status
```

#### 3. Static Files Not Loading
- Ensure `whitenoise` is in requirements.txt
- Check `config/config_production.py` for static settings

#### 4. Memory Issues (R14)
```bash
heroku ps:scale web=1:standard-1x
# Upgrade to larger dyno if needed
```

### Useful Commands
```bash
# Restart application
heroku restart

# Run Django shell
heroku run python

# Check release status
heroku releases

# Rollback to previous version
heroku rollback
```

## Scaling & Production

### Dyno Scaling Options

#### Hobby Tier (Current)
- **Cost**: ~$7/month per dyno
- **Features**: Always-on, SSL, Custom domains
- **Good for**: Small teams, testing
```bash
heroku ps:scale web=1:hobby
```

#### Production Tier
- **Cost**: $25-500/month per dyno
- **Features**: Horizontal scaling, Metrics, Autoscaling
- **Good for**: Business use, high traffic
```bash
heroku ps:scale web=1:standard-1x
# Or for high performance:
heroku ps:scale web=2:performance-m
```

### Database Scaling

#### Current: mini ($5/month)
- 1GB storage
- 20 connections
- Good for small teams

#### Upgrade Options:
```bash
# Basic ($9/month) - 10GB storage
heroku addons:upgrade heroku-postgresql:basic

# Standard ($50/month) - 64GB storage, follower support
heroku addons:upgrade heroku-postgresql:standard-0
```

### Security Enhancements

1. **Force HTTPS**
   ```python
   # Already configured in production settings
   SECURE_SSL_REDIRECT = True
   ```

2. **Add Custom Domain**
   ```bash
   heroku domains:add www.the5hc.com
   ```

3. **Enable Automated Backups**
   ```bash
   heroku pg:backups:schedule --at '02:00 Asia/Seoul'
   ```

## Production-Ready Features

### Security
- ✅ BCrypt password hashing
- ✅ Session timeout (24 hours)
- ✅ Rate limiting on login attempts
- ✅ SQL injection prevention
- ✅ HTTPS enforcement (Heroku provides)

### Performance
- ✅ Database connection pooling
- ✅ Query optimization for PostgreSQL
- ✅ Static file compression
- ✅ Efficient session management
- ✅ Caching configuration ready

### Reliability
- ✅ Comprehensive error handling
- ✅ Automatic database migrations
- ✅ Health check endpoint
- ✅ Graceful error pages
- ✅ Detailed logging

### User Experience
- ✅ Korean language UI
- ✅ Responsive design
- ✅ Fast page loads
- ✅ Intuitive navigation
- ✅ Professional appearance

## Summary

The5HC is fully configured and ready for production deployment on Heroku. All critical features have been implemented, tested, and optimized for the production environment. The application will automatically handle the SQLite to PostgreSQL transition and create all necessary database tables on first run.

**Next Steps After Deployment:**
1. Monitor application logs for the first 24 hours
2. Test all features in production environment
3. Set up automated backups
4. Configure custom domain (if desired)
5. Plan for scaling based on usage

For additional support or questions, refer to:
- [Heroku Documentation](https://devcenter.heroku.com/)
- Application logs: `heroku logs --tail`
- Database status: `heroku pg:info`