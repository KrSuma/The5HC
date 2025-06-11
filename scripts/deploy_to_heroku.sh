#!/bin/bash

# The5HC Heroku Deployment Script
# This script helps deploy the Django application to Heroku

echo "🚀 Starting The5HC Heroku Deployment..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first."
    echo "   macOS: brew tap heroku/brew && brew install heroku"
    echo "   Other: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "🔐 Please log in to Heroku..."
    heroku login
fi

# Set variables
APP_NAME="the5hc-fitness"
HEROKU_REMOTE="heroku"

# Function to check if app exists
app_exists() {
    heroku apps:info --app "$APP_NAME" &> /dev/null
}

# Create app if it doesn't exist
if ! app_exists; then
    echo "📱 Creating Heroku app: $APP_NAME"
    heroku create "$APP_NAME"
else
    echo "✅ App $APP_NAME already exists"
fi

# Add git remote if not exists
if ! git remote | grep -q "$HEROKU_REMOTE"; then
    echo "🔗 Adding Heroku remote..."
    heroku git:remote -a "$APP_NAME"
else
    echo "✅ Heroku remote already configured"
fi

# Check if PostgreSQL addon exists
if ! heroku addons --app "$APP_NAME" | grep -q "heroku-postgresql"; then
    echo "🐘 Adding PostgreSQL database..."
    heroku addons:create heroku-postgresql:mini --app "$APP_NAME"
else
    echo "✅ PostgreSQL addon already exists"
fi

# Add buildpack for WeasyPrint dependencies
echo "📦 Configuring buildpacks..."
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt --app "$APP_NAME" 2>/dev/null || echo "✅ Apt buildpack already added"
heroku buildpacks:add heroku/python --app "$APP_NAME" 2>/dev/null || echo "✅ Python buildpack already added"

# Set environment variables
echo "🔧 Setting environment variables..."

# Generate a secure secret key if needed
if [[ -z "$SECRET_KEY" ]]; then
    SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
fi

heroku config:set \
    DJANGO_SETTINGS_MODULE=the5hc.settings.production \
    SECRET_KEY="$SECRET_KEY" \
    ALLOWED_HOSTS="$APP_NAME.herokuapp.com" \
    DEBUG=False \
    --app "$APP_NAME"

echo "📋 Current configuration:"
heroku config --app "$APP_NAME"

# Confirm before deploying
echo ""
echo "🎯 Ready to deploy to Heroku!"
echo "   App: $APP_NAME"
echo "   URL: https://$APP_NAME.herokuapp.com"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Deploy to Heroku
    echo "🚀 Deploying to Heroku..."
    git push "$HEROKU_REMOTE" main
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Create superuser: heroku run python manage.py createsuperuser --app $APP_NAME"
    echo "2. View logs: heroku logs --tail --app $APP_NAME"
    echo "3. Open app: heroku open --app $APP_NAME"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "- Check logs: heroku logs --tail --app $APP_NAME"
    echo "- Run shell: heroku run python manage.py shell --app $APP_NAME"
    echo "- Database info: heroku pg:info --app $APP_NAME"
else
    echo "❌ Deployment cancelled"
fi