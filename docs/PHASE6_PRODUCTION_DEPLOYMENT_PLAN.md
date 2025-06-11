# Phase 6: Django Production Deployment Plan

**Date**: 2025-01-11
**Author**: Claude
**Project**: The5HC Django Migration
**Target Platform**: Heroku with PostgreSQL

## Executive Summary

This document outlines the comprehensive plan for deploying the Django migration of The5HC fitness assessment system to production on Heroku. The deployment will replace the existing Streamlit application with a fully-featured Django application including web UI and RESTful API.

## Current Status

### Migration Progress
- ✅ Phase 1-5: Complete (Django setup, models, UI, PDF generation, API, testing)
- 🔲 Phase 6: Production deployment (This plan)

### Test Suite Status
- Total Tests: 166
- Passing: 120 (72.3%)
- Remaining failures mainly due to unimplemented features

### Key Components Ready
- Django 5.0.1 with HTMX/Alpine.js frontend
- RESTful API with JWT authentication
- PDF report generation
- Data migration scripts (42 records migrated)
- Korean localization

## Pre-Deployment Checklist

### 1. Code Quality & Testing
- [ ] Fix critical test failures (minimum 90% pass rate)
- [ ] Run security audit with `pip-audit`
- [ ] Verify all sensitive data is in environment variables
- [ ] Review and update all hardcoded URLs/paths
- [ ] Ensure DEBUG=False works correctly
- [ ] Test with production settings locally

### 2. Database Preparation
- [ ] Backup existing Streamlit production database
- [ ] Verify PostgreSQL compatibility in all queries
- [ ] Test data migration scripts with production data copy
- [ ] Prepare rollback scripts
- [ ] Document any manual data fixes needed

### 3. Static Assets & Media
- [ ] Verify all static files are collected
- [ ] Test WhiteNoise configuration
- [ ] Ensure fonts are included for PDF generation
- [ ] Configure media file storage (if needed)
- [ ] Test file upload functionality

### 4. Security Hardening
- [ ] Generate new SECRET_KEY for production
- [ ] Configure ALLOWED_HOSTS correctly
- [ ] Set up CSRF_TRUSTED_ORIGINS
- [ ] Enable all security middleware
- [ ] Configure CORS settings for API
- [ ] Review authentication rate limiting

## Environment Variables

### Required Production Environment Variables

```bash
# Django Core
SECRET_KEY=<generate-new-secure-key>
DEBUG=False
DJANGO_SETTINGS_MODULE=the5hc.settings.production

# Database (automatically set by Heroku)
DATABASE_URL=postgres://...

# Allowed Hosts
ALLOWED_HOSTS=your-app.herokuapp.com,www.yourdomain.com

# CSRF & CORS
CSRF_TRUSTED_ORIGINS=https://your-app.herokuapp.com,https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://your-frontend-app.com

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Logging
LOG_LEVEL=INFO

# Redis Cache (Optional)
REDIS_URL=redis://...

# JWT Settings (if different from defaults)
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=10080
```

## Deployment Files Setup

### 1. Create Procfile
```procfile
web: gunicorn the5hc.wsgi --log-file -
release: python manage.py migrate && python manage.py collectstatic --noinput
```

### 2. Update runtime.txt
```
python-3.11.10
```

### 3. Create .env.example
```bash
# Copy this to .env and fill in values
SECRET_KEY=your-secret-key-here
DEBUG=False
DATABASE_URL=postgres://...
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Step-by-Step Deployment Process

### Phase 1: Local Preparation (Day 1)

1. **Create deployment branch**
   ```bash
   git checkout -b django-production-deployment
   cd django_migration
   ```

2. **Install and test with production settings**
   ```bash
   pip install -r requirements.txt
   export DJANGO_SETTINGS_MODULE=the5hc.settings.production
   python manage.py check --deploy
   ```

3. **Run security audit**
   ```bash
   pip install pip-audit
   pip-audit
   ```

4. **Generate static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Test with gunicorn locally**
   ```bash
   gunicorn the5hc.wsgi:application --bind 0.0.0.0:8000
   ```

### Phase 2: Heroku Setup (Day 1)

1. **Create new Heroku app**
   ```bash
   heroku create the5hc-django
   ```

2. **Add PostgreSQL addon**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. **Configure environment variables**
   ```bash
   heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
   heroku config:set DJANGO_SETTINGS_MODULE=the5hc.settings.production
   heroku config:set ALLOWED_HOSTS=the5hc-django.herokuapp.com
   heroku config:set CSRF_TRUSTED_ORIGINS=https://the5hc-django.herokuapp.com
   ```

4. **Add buildpacks**
   ```bash
   heroku buildpacks:add heroku/python
   ```

### Phase 3: Database Migration (Day 2)

1. **Backup current production data**
   ```bash
   # From existing Streamlit app
   heroku pg:backups:capture --app current-streamlit-app
   heroku pg:backups:download --app current-streamlit-app
   ```

2. **Create staging database**
   ```bash
   heroku addons:create heroku-postgresql:mini --as STAGING_DATABASE
   ```

3. **Test migration on staging**
   ```bash
   # Restore backup to staging
   heroku pg:backups:restore <backup-url> STAGING_DATABASE --app the5hc-django
   
   # Run Django migrations
   heroku run python manage.py migrate --app the5hc-django
   
   # Run data migration script
   heroku run python scripts/migrate_data_from_streamlit.py --app the5hc-django
   ```

4. **Verify data integrity**
   ```bash
   heroku run python manage.py shell --app the5hc-django
   # Run verification queries
   ```

### Phase 4: Initial Deployment (Day 2)

1. **Deploy to Heroku**
   ```bash
   git add -A
   git commit -m "Phase 6: Production deployment configuration"
   git push heroku django-production-deployment:main
   ```

2. **Monitor deployment**
   ```bash
   heroku logs --tail --app the5hc-django
   ```

3. **Run post-deployment commands**
   ```bash
   # Create superuser
   heroku run python manage.py createsuperuser --app the5hc-django
   
   # Compile messages for Korean locale
   heroku run python manage.py compilemessages --app the5hc-django
   ```

### Phase 5: Verification (Day 3)

1. **Functional Testing**
   - [ ] Test login/logout functionality
   - [ ] Verify client CRUD operations
   - [ ] Test assessment creation and scoring
   - [ ] Verify PDF report generation
   - [ ] Test API endpoints with JWT auth
   - [ ] Check session management and payments
   - [ ] Verify Korean language display

2. **Performance Testing**
   - [ ] Load test with Apache Bench or similar
   - [ ] Monitor database query performance
   - [ ] Check static file loading times
   - [ ] Verify API response times

3. **Security Testing**
   - [ ] Test for SQL injection vulnerabilities
   - [ ] Verify CSRF protection
   - [ ] Check authentication flows
   - [ ] Test rate limiting
   - [ ] Verify HTTPS enforcement

### Phase 6: DNS & Final Switch (Day 3)

1. **Update DNS (if using custom domain)**
   ```bash
   heroku domains:add www.yourdomain.com --app the5hc-django
   ```

2. **Set up SSL certificate**
   ```bash
   heroku certs:auto:enable --app the5hc-django
   ```

3. **Switch production traffic**
   - Update DNS records to point to new app
   - Monitor for any issues
   - Keep old app running for quick rollback

## Post-Deployment Tasks

### 1. Monitoring Setup

1. **Enable Heroku metrics**
   ```bash
   heroku labs:enable log-runtime-metrics --app the5hc-django
   ```

2. **Set up error tracking (Sentry)**
   ```bash
   heroku addons:create sentry --app the5hc-django
   ```

3. **Configure application monitoring**
   ```bash
   heroku addons:create newrelic:wayne --app the5hc-django
   ```

### 2. Backup Configuration

1. **Schedule daily backups**
   ```bash
   heroku pg:backups:schedule DATABASE_URL --at '02:00 Asia/Seoul' --app the5hc-django
   ```

2. **Set backup retention**
   ```bash
   heroku pg:backups:retention DATABASE_URL --days 7 --app the5hc-django
   ```

### 3. Performance Optimization

1. **Enable database connection pooling**
   - Already configured in production.py with conn_max_age=600

2. **Configure Redis caching (optional)**
   ```bash
   heroku addons:create heroku-redis:mini --app the5hc-django
   ```

3. **Enable Django caching**
   - Cache configuration already in settings

## Rollback Procedures

### Quick Rollback (< 5 minutes)

1. **Revert to previous release**
   ```bash
   heroku releases --app the5hc-django
   heroku rollback v<previous-version> --app the5hc-django
   ```

### Database Rollback (< 30 minutes)

1. **Restore from backup**
   ```bash
   heroku pg:backups --app the5hc-django
   heroku pg:backups:restore <backup-id> DATABASE_URL --app the5hc-django
   ```

### Complete Rollback to Streamlit (< 1 hour)

1. **Switch DNS back to old app**
2. **Restore database if needed**
3. **Communicate with users about temporary reversion**

## Security Considerations

### 1. Production Security Checklist
- [x] DEBUG=False in production
- [x] SECRET_KEY from environment variable
- [x] ALLOWED_HOSTS configured
- [x] CSRF protection enabled
- [x] XSS protection headers
- [x] HTTPS enforcement
- [x] Secure cookies
- [x] HSTS headers
- [ ] Content Security Policy (optional)
- [ ] Database SSL enforcement

### 2. API Security
- [x] JWT authentication configured
- [x] API rate limiting (via Django REST framework)
- [x] CORS properly configured
- [ ] API key management (if needed)
- [ ] Request signing (if needed)

### 3. Data Protection
- [x] Bcrypt password hashing
- [x] Session timeout (24 hours)
- [x] Login attempt rate limiting
- [ ] Two-factor authentication (future)
- [ ] Data encryption at rest (Heroku managed)

## Communication Plan

### 1. Pre-Deployment (1 week before)
- Notify users of upcoming system upgrade
- Provide expected downtime window (2-4 hours)
- Share new features and improvements

### 2. During Deployment
- Display maintenance page on old system
- Update status page every hour
- Have support team ready for issues

### 3. Post-Deployment
- Send confirmation email to all users
- Provide quick start guide for new features
- Monitor support channels for issues

## Risk Mitigation

### High-Risk Areas
1. **Data Migration**: Test thoroughly on staging
2. **Authentication**: Ensure all users can log in
3. **PDF Generation**: Verify fonts and dependencies
4. **API Integration**: Test with any external systems

### Contingency Plans
1. **Partial Failure**: Run both systems in parallel
2. **Performance Issues**: Scale dynos temporarily
3. **Data Corruption**: Restore from hourly backups
4. **Complete Failure**: Rollback to Streamlit

## Success Criteria

### Deployment is successful when:
1. All users can log in and access their data
2. Core functionality works without errors
3. Performance meets or exceeds Streamlit app
4. No data loss or corruption
5. API endpoints respond correctly
6. PDF reports generate properly
7. Korean language displays correctly

## Timeline

### Day 1: Preparation
- Morning: Code review and security audit
- Afternoon: Heroku setup and configuration

### Day 2: Migration
- Morning: Database backup and staging test
- Afternoon: Initial deployment and testing

### Day 3: Go-Live
- Morning: Final verification and monitoring setup
- Afternoon: DNS switch and production launch
- Evening: Post-deployment monitoring

## Appendix: Useful Commands

### Heroku Management
```bash
# View app info
heroku info --app the5hc-django

# View logs
heroku logs --tail --app the5hc-django

# Run Django shell
heroku run python manage.py shell --app the5hc-django

# Database info
heroku pg:info --app the5hc-django

# Scale dynos
heroku ps:scale web=2 --app the5hc-django
```

### Django Management
```bash
# Check deployment readiness
python manage.py check --deploy

# Show migrations
python manage.py showmigrations

# Create cache table
python manage.py createcachetable

# Collect static files
python manage.py collectstatic --noinput
```

### Monitoring
```bash
# View metrics
heroku metrics --app the5hc-django

# Database queries
heroku pg:diagnose --app the5hc-django

# View releases
heroku releases --app the5hc-django
```

## Next Steps

1. Review and approve this deployment plan
2. Schedule deployment window with stakeholders
3. Prepare user communications
4. Set up staging environment for final testing
5. Create detailed runbook for deployment day

---

This deployment plan provides a comprehensive roadmap for successfully deploying the Django migration to production. The phased approach minimizes risk while ensuring all critical aspects are covered.