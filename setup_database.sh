#!/bin/bash
# Database setup script for deployment

echo "🗄️ Setting up Arabic Dictionary Database"
echo "========================================"

# Check if database exists
if [ -f "dict.db" ]; then
    echo "✅ Database already exists ($(du -h dict.db | cut -f1))"
    echo "📊 Verifying database content..."
    
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('dict.db')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM entries')
    entries = cur.fetchone()[0]
    print(f'✅ Entries: {entries:,}')
    conn.close()
    if entries > 70000:
        print('✅ Database verification successful')
    else:
        print('❌ Database appears incomplete')
        exit(1)
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"
else
    echo "❌ Database not found!"
    echo "📥 For deployment, the database should be:"
    echo "   1. Uploaded to cloud storage (Google Drive, Dropbox, etc.)"
    echo "   2. Downloaded during build process"
    echo "   3. Or use a hosted database service"
    echo ""
    echo "🔗 Database download URL should be set in environment variable:"
    echo "   DATABASE_DOWNLOAD_URL=https://your-storage-url/dict.db"
    
    if [ ! -z "$DATABASE_DOWNLOAD_URL" ]; then
        echo "📥 Downloading database from: $DATABASE_DOWNLOAD_URL"
        curl -L -o dict.db "$DATABASE_DOWNLOAD_URL"
        
        if [ -f "dict.db" ]; then
            echo "✅ Database downloaded successfully"
        else
            echo "❌ Database download failed"
            exit 1
        fi
    else
        echo "❌ No DATABASE_DOWNLOAD_URL provided"
        exit 1
    fi
fi

echo "🚀 Database setup complete!"
