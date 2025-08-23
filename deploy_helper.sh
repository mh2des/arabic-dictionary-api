#!/bin/bash
# Deployment helper script for Arabic Dictionary API

echo "🚀 Arabic Dictionary API - Deployment Helper"
echo "==========================================="

echo "📁 Current project structure:"
ls -la

echo ""
echo "📊 Database verification:"
python -c "
import sqlite3
conn = sqlite3.connect('dict.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM entries')
entries = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM dialects')
dialects = cur.fetchone()[0]
print(f'✅ Entries: {entries:,}')
print(f'✅ Dialects: {dialects}')
conn.close()
"

echo ""
echo "🔧 Testing API..."
python -c "
import sys, os
sys.path.append('.')
from api.main import app
print('✅ API imports successfully')
print('✅ Ready for deployment')
"

echo ""
echo "📋 Next steps for Render deployment:"
echo "1. Initialize git: git init"
echo "2. Add files: git add ."
echo "3. Commit: git commit -m 'Initial commit - Arabic Dictionary API'"
echo "4. Push to GitHub repository"
echo "5. Connect to Render and deploy"
echo ""
echo "🌟 Your API will be available at: https://your-service-name.onrender.com"
echo "📚 Documentation will be at: https://your-service-name.onrender.com/docs"
