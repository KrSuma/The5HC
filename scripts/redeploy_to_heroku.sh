#!/bin/bash

# The5HC Heroku Redeployment Script
# This script helps redeploy the Django application to existing Heroku app

echo "🔄 Starting The5HC Heroku Redeployment..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first."
    exit 1
fi

# Variables
APP_NAME="the5hc-fitness"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

# Check Heroku remote
echo "🔍 Checking Heroku remote..."
if ! git remote | grep -q "heroku"; then
    echo "📎 Adding Heroku remote..."
    heroku git:remote -a "$APP_NAME"
fi

# Show current Heroku app info
echo "📊 Current Heroku app info:"
heroku apps:info --app "$APP_NAME" 2>/dev/null || {
    echo "❌ Error: App $APP_NAME not found. Please check the app name."
    exit 1
}

# Check for uncommitted changes
echo ""
echo "📝 Git status:"
if [[ -n $(git status -s) ]]; then
    echo "⚠️  You have uncommitted changes. You should commit them before deploying."
    echo ""
    git status -s
    echo ""
    read -p "Do you want to commit all changes now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        echo "Enter commit message: "
        read commit_message
        git commit -m "$commit_message"
    else
        echo "⚠️  Warning: Deploying without committing local changes."
    fi
else
    echo "✅ Working directory clean"
fi

# Update buildpacks if needed
echo ""
echo "📦 Checking buildpacks..."
if ! heroku buildpacks --app "$APP_NAME" | grep -q "heroku-buildpack-apt"; then
    echo "Adding apt buildpack for WeasyPrint..."
    heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt --app "$APP_NAME"
fi

# Show current config
echo ""
echo "🔧 Current configuration:"
heroku config --app "$APP_NAME" | grep -E "(DJANGO_SETTINGS_MODULE|DEBUG|DATABASE_URL)"

# Ask if user wants to update any config
echo ""
read -p "Do you need to update any environment variables? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Setting production environment variables..."
    heroku config:set \
        DJANGO_SETTINGS_MODULE=the5hc.settings.production \
        DEBUG=False \
        --app "$APP_NAME"
fi

# Confirm deployment
echo ""
echo "🎯 Ready to redeploy to Heroku!"
echo "   App: $APP_NAME"
echo "   Git remote: $(git remote get-url heroku 2>/dev/null || echo 'Not set')"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Deploy to Heroku
    echo "🚀 Deploying to Heroku..."
    git push heroku main --force
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    
    # Show post-deployment options
    echo "📋 Post-deployment actions:"
    echo "1. View logs: heroku logs --tail --app $APP_NAME"
    echo "2. Run migrations manually: heroku run python manage.py migrate --app $APP_NAME"
    echo "3. Create/update superuser: heroku run python manage.py createsuperuser --app $APP_NAME"
    echo "4. Open app: heroku open --app $APP_NAME"
    echo "5. Check database: heroku pg:info --app $APP_NAME"
    echo ""
    
    # Ask if user wants to see logs
    read -p "View deployment logs now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        heroku logs --tail --app "$APP_NAME"
    fi
else
    echo "❌ Deployment cancelled"
fi