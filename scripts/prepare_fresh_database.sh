#!/bin/bash

# The5HC Fresh Database Setup Script
# This script backs up the existing database and prepares a fresh one for Django

echo "🗄️ Preparing Fresh PostgreSQL Database for Django..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first."
    exit 1
fi

# Variables
APP_NAME="the5hc-fitness"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Function to check if app exists
app_exists() {
    heroku apps:info --app "$APP_NAME" &> /dev/null
}

# Check if app exists
if ! app_exists; then
    echo "❌ App $APP_NAME not found. Please check the app name."
    exit 1
fi

echo "📊 Current database info:"
heroku pg:info --app "$APP_NAME"

# Create backup of existing database
echo ""
echo "💾 Creating backup of existing database..."
echo "This backup will be saved as: backup_${BACKUP_DATE}"

heroku pg:backups:capture --app "$APP_NAME"

echo ""
echo "📋 Recent backups:"
heroku pg:backups --app "$APP_NAME"

# Ask for confirmation before proceeding
echo ""
echo "⚠️  WARNING: The following actions will COMPLETELY WIPE the existing database!"
echo "   - All existing data will be deleted"
echo "   - A fresh database will be created for Django"
echo "   - You can restore from backup if needed"
echo ""
read -p "Are you sure you want to continue? Type 'yes' to proceed: " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "❌ Operation cancelled"
    exit 1
fi

# Option 1: Reset the database (keeps the same database URL)
echo ""
echo "🔄 Resetting database..."
heroku pg:reset DATABASE_URL --app "$APP_NAME" --confirm "$APP_NAME"

echo ""
echo "✅ Database has been reset and is ready for Django!"
echo ""
echo "📋 Next steps:"
echo "1. Deploy your Django application:"
echo "   git push heroku main"
echo ""
echo "2. The Django migrations will run automatically via Procfile"
echo "   If they don't, run manually:"
echo "   heroku run python manage.py migrate --app $APP_NAME"
echo ""
echo "3. Create a Django superuser:"
echo "   heroku run python manage.py createsuperuser --app $APP_NAME"
echo ""
echo "4. (Optional) Load initial data:"
echo "   heroku run python manage.py loaddata initial_data.json --app $APP_NAME"
echo ""
echo "💡 Backup Information:"
echo "   - Your backup was created successfully"
echo "   - To view backups: heroku pg:backups --app $APP_NAME"
echo "   - To restore: heroku pg:backups:restore [BACKUP_ID] DATABASE_URL --app $APP_NAME"
echo ""
echo "🔍 To verify the clean database:"
echo "   heroku run python manage.py dbshell --app $APP_NAME"
echo "   Then run: \\dt (to list tables - should be empty)"