#!/bin/bash
# Set environment variables for WeasyPrint on macOS
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH"
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"

# Run the Streamlit app
cd /Users/jslee/PycharmProjects/The5HC
python3 -m streamlit run main.py --server.port 8501 --server.address localhost