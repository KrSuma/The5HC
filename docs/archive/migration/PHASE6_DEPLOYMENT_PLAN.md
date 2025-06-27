# Phase 6: Production Deployment Plan

**Date**: January 11, 2025  
**Author**: Claude  
**Status**: In Progress

## Overview

This document outlines the deployment process for The5HC Django application to Heroku. The application has been fully migrated from Streamlit to Django and is ready for production deployment.

## Pre-Deployment Checklist

### ✅ Completed
- [x] Django application fully migrated to root directory
- [x] All 7 Django apps functional (accounts, analytics, api, assessments, clients, reports, sessions)
- [x] Database models and migrations complete
- [x] HTMX + Alpine.js frontend implementation
- [x] RESTful API with JWT authentication
- [x] PDF report generation with WeasyPrint
- [x] Korean language support
- [x] Python updated to 3.12.1
- [x] Procfile updated for root directory structure
- [x] runtime.txt updated to python-3.12.1

### ⏳ To Be Completed
- [ ] Configure production environment variables
- [ ] Set up Heroku PostgreSQL database
- [ ] Configure allowed hosts and CORS settings
- [ ] Set up static file serving with WhiteNoise
- [ ] Configure email settings (optional)
- [ ] Run production migrations
- [ ] Verify all features in production

## Deployment Steps

### Step 1: Heroku Setup

```bash
# Install Heroku CLI if not already installed
# macOS: brew tap heroku/brew && brew install heroku

# Login to Heroku
heroku login

# Create new Heroku app (if not exists)
heroku create the5hc-fitness

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini
```

### Step 2: Environment Variables

Required environment variables for production:

```bash
# Django settings
heroku config:set DJANGO_SETTINGS_MODULE=the5hc.settings.production
heroku config:set SECRET_KEY='your-secure-secret-key-here'
heroku config:set ALLOWED_HOSTS='the5hc-fitness.herokuapp.com'

# Database (automatically set by Heroku PostgreSQL addon)
# DATABASE_URL=postgres://...

# Optional: Email configuration
# heroku config:set EMAIL_HOST='smtp.gmail.com'
# heroku config:set EMAIL_HOST_USER='your-email@gmail.com'
# heroku config:set EMAIL_HOST_PASSWORD='your-app-password'

# Optional: Debug (set to False for production)
heroku config:set DEBUG=False
```

### Step 3: Update Production Settings

Verify `the5hc/settings/production.py`:
- ALLOWED_HOSTS includes Heroku domain
- Static files configuration with WhiteNoise
- Database configuration using dj_database_url
- Security settings enabled

### Step 4: Static Files Setup

```bash
# Collect static files locally to verify
python manage.py collectstatic --noinput

# Verify WhiteNoise middleware is configured
# Check STATICFILES_STORAGE in production.py
```

### Step 5: Deploy to Heroku

```bash
# Add Heroku remote (if not already added)
heroku git:remote -a the5hc-fitness

# Deploy to Heroku
git add .
git commit -m "Phase 6: Configure Django application for Heroku deployment"
git push heroku main

# Monitor deployment logs
heroku logs --tail
```

### Step 6: Post-Deployment Tasks

```bash
# Run migrations (automatic via release command in Procfile)
# Verify with: heroku run python manage.py showmigrations

# Create superuser
heroku run python manage.py createsuperuser

# Load initial data (if needed)
# heroku run python scripts/migrate_data_from_streamlit.py

# Open application
heroku open
```

### Step 7: Verify Production Features

1. **Authentication**
   - Test login/logout functionality
   - Verify session persistence
   - Check password reset (if email configured)

2. **Client Management**
   - Create, read, update, delete clients
   - Search and filter functionality
   - CSV export

3. **Assessments**
   - Create new assessments
   - Multi-step form workflow
   - Score calculations
   - Chart visualizations

4. **Session Management**
   - Create session packages
   - Schedule sessions
   - Payment tracking
   - Calendar view

5. **Reports**
   - Generate PDF reports
   - Verify Korean font rendering
   - Download functionality

6. **API**
   - Test JWT authentication
   - Verify all endpoints
   - Check API documentation at /api/v1/docs/

## Troubleshooting

### Common Issues

1. **Static Files Not Loading**
   - Verify WhiteNoise configuration
   - Check STATIC_ROOT and STATIC_URL settings
   - Run `collectstatic` command

2. **Database Connection Errors**
   - Check DATABASE_URL is set
   - Verify PostgreSQL addon is provisioned
   - Check connection settings in production.py

3. **Import Errors**
   - Ensure all dependencies in requirements.txt
   - Check for missing migrations
   - Verify PYTHONPATH settings

4. **PDF Generation Issues**
   - WeasyPrint requires additional buildpacks
   - Add: `heroku buildpacks:add https://github.com/heroku/heroku-buildpack-apt`
   - Create Aptfile with: `libpango-1.0-0 libpangocairo-1.0-0`

### Monitoring

```bash
# View application logs
heroku logs --tail

# Check application metrics
heroku ps

# Run Django shell
heroku run python manage.py shell

# Check database
heroku pg:info
```

## Rollback Procedure

If deployment fails:

```bash
# View releases
heroku releases

# Rollback to previous version
heroku rollback v[previous-version]

# Investigate issues
heroku logs --tail
```

## Security Checklist

- [ ] SECRET_KEY is unique and secure
- [ ] DEBUG is False
- [ ] ALLOWED_HOSTS is properly configured
- [ ] HTTPS is enforced (SECURE_SSL_REDIRECT)
- [ ] CSRF and session cookies are secure
- [ ] No sensitive data in logs
- [ ] Database backups configured

## Next Steps After Deployment

1. Set up continuous deployment with GitHub Actions
2. Configure monitoring (Sentry, New Relic)
3. Set up database backups
4. Configure custom domain (if needed)
5. Set up staging environment
6. Create user documentation

## Success Criteria

- [ ] Application accessible via Heroku URL
- [ ] All pages load without errors
- [ ] Database operations work correctly
- [ ] PDF generation functional
- [ ] API endpoints respond correctly
- [ ] No console errors in browser
- [ ] Performance acceptable (< 3s page loads)