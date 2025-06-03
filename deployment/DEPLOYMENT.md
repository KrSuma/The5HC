# Heroku Deployment Guide

## Prerequisites

1. Heroku CLI installed
2. Git repository initialized
3. Heroku account

## Deployment Steps

### 1. Create Heroku App

```bash
heroku create your-fitness-app-name
```

### 2. Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:mini
```

### 3. Set Environment Variables (Optional)

```bash
heroku config:set DEBUG=false
heroku config:set LOG_LEVEL=INFO
heroku config:set SECRET_KEY="your-super-secure-secret-key"
```

### 4. Deploy to Heroku

```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### 5. Run Database Migration

The migration runs automatically during deployment via the `release` command in Procfile.
To run manually:

```bash
heroku run python migrate_database.py
```

### 6. Open Application

```bash
heroku open
```

## Important Files for Deployment

- `Procfile`: Defines how Heroku runs your app
- `requirements.txt`: Python dependencies
- `runtime.txt`: Python version
- `migrate_database.py`: Database setup script
- `database_config.py`: Database configuration
- `.streamlit/config.toml`: Streamlit configuration

## Environment Variables

The app automatically detects production environment via `DATABASE_URL` environment variable set by Heroku PostgreSQL addon.

### Required Environment Variables (Auto-set by Heroku):
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Port number for the web server

### Optional Environment Variables:
- `DEBUG`: Set to 'true' for debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: INFO)
- `SECRET_KEY`: Secret key for sessions (auto-generated if not set)

## Database

- **Development**: SQLite (`data/fitness_assessment.db`)
- **Production**: PostgreSQL (via Heroku add-on)

The app automatically switches between databases based on the presence of `DATABASE_URL`.

## Features

- Automatic database migration on deployment
- Persistent PostgreSQL database on Heroku
- Production-ready security settings
- Optimized requirements with pinned versions
- Proper logging configuration

## Troubleshooting

### Check Logs
```bash
heroku logs --tail
```

### Database Issues
```bash
heroku pg:info
heroku run python migrate_database.py
```

### App Issues
```bash
heroku restart
heroku ps
```

## Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Database | SQLite | PostgreSQL |
| Debug Mode | True | False |
| Logging | Console + File | Heroku Logs |
| CORS | Enabled | Disabled |
| File Storage | Local | Heroku Ephemeral |

## Security Notes

1. Never commit sensitive data to Git
2. Use environment variables for secrets
3. Keep dependencies updated
4. Monitor Heroku security advisories
5. Use HTTPS in production (Heroku provides this)

## Scaling

- **Hobby Tier**: Free, sleeps after 30 min of inactivity
- **Production Tier**: Always on, more resources
- **Database**: Start with hobby-dev, upgrade as needed

```bash
# Upgrade to production tier
heroku ps:scale web=1:standard-1x

# Upgrade database
heroku addons:create heroku-postgresql:standard-0
```