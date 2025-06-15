#!/bin/bash

# Run Django with WeasyPrint support on macOS
# This script sets up the necessary environment variables for WeasyPrint

echo "Setting up environment for WeasyPrint on macOS..."

# Set the library path for WeasyPrint dependencies
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Check if required dependencies are installed
if ! brew list cairo &>/dev/null; then
    echo "WARNING: cairo is not installed. Install with: brew install cairo"
fi

if ! brew list pango &>/dev/null; then
    echo "WARNING: pango is not installed. Install with: brew install pango"
fi

if ! brew list gdk-pixbuf &>/dev/null; then
    echo "WARNING: gdk-pixbuf is not installed. Install with: brew install gdk-pixbuf"
fi

if ! brew list libffi &>/dev/null; then
    echo "WARNING: libffi is not installed. Install with: brew install libffi"
fi

if ! brew list glib &>/dev/null; then
    echo "WARNING: glib is not installed. Install with: brew install glib"
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found. Using system Python."
fi

# Run Django development server
echo "Starting Django development server with WeasyPrint support..."
python manage.py runserver

# Alternative: Run with specific host and port
# python manage.py runserver 0.0.0.0:8000