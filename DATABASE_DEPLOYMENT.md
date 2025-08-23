# 🗄️ Database Deployment Strategy

## Problem: Large Database File (1.5GB)
GitHub has a 100MB file limit, but our database is 1.5GB with 74,977 entries.

## 🚀 Solution Options for Render Deployment

### Option 1: Upload Database to Cloud Storage (Recommended)
1. **Upload dict.db to Google Drive/Dropbox**:
   - Upload `dict.db` to Google Drive
   - Get shareable link (make sure it's publicly accessible)
   - Use direct download link format

2. **Set Environment Variable in Render**:
   ```
   DATABASE_DOWNLOAD_URL=https://your-direct-download-link
   ```

3. **Update render.yaml**:
   ```yaml
   buildCommand: |
     pip install -r requirements.txt
     curl -L -o dict.db $DATABASE_DOWNLOAD_URL
   ```

### Option 2: Use Git LFS (GitHub Large File Storage)
```bash
# Install Git LFS
git lfs install

# Track the database file
git lfs track "*.db"
git add .gitattributes
git add dict.db
git commit -m "Add database with LFS"
git push origin master
```

### Option 3: Deploy Without Database (Create Empty)
For testing purposes, you can deploy with an empty database:

```python
# In api/main.py, add database creation
import sqlite3
import os

def ensure_database():
    if not os.path.exists("dict.db"):
        # Create minimal database structure
        conn = sqlite3.connect("dict.db")
        cur = conn.cursor()
        cur.execute("CREATE TABLE entries (id TEXT PRIMARY KEY, lemma_surface TEXT)")
        cur.execute("INSERT INTO entries VALUES ('test::noun', 'اختبار')")
        conn.commit()
        conn.close()
        print("Created minimal database for testing")

# Call before starting the app
ensure_database()
```

## 🎯 Recommended Approach

### For Immediate Deployment:
1. **Use Google Drive**:
   - Upload `dict.db` to Google Drive
   - Share with "Anyone with link can view"
   - Get direct download link
   - Set in Render environment variables

### For Production:
1. **Consider hosted database**:
   - PostgreSQL on Render
   - CloudSQL
   - Amazon RDS
   - Import data during deployment

## 📝 Implementation Steps

1. **Commit code without database**:
   ```bash
   git add .
   git commit -m "Arabic Dictionary API - ready for deployment"
   git push origin master
   ```

2. **Deploy to Render**:
   - Connect GitHub repository
   - Add environment variable for database URL
   - Deploy

3. **Verify deployment**:
   - Check `/health` endpoint
   - Test `/stats` endpoint
   - Verify API functionality

## 🔗 Current Status
- ✅ Database excluded from git (too large)
- ✅ API code ready for deployment
- ✅ Environment configured for database download
- ✅ Health checks implemented

Choose your preferred option and proceed with deployment!
