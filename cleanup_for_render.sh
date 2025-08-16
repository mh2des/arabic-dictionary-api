#!/bin/bash

# Clean up unnecessary files for Render deployment
echo "🧹 Cleaning up for Render deployment..."

# Remove Railway-specific files
rm -f railway.json
rm -f Procfile
rm -f nixpacks.toml
rm -f start_railway.py
rm -f deploy_to_railway.py
rm -f upload_db_to_railway.py

# Remove development/test files
rm -f test_*.py
rm -f debug_*.py
rm -f check_*.py
rm -f show_*.py
rm -f analyze_*.py
rm -f enhance_*.py
rm -f phase*.py
rm -f option_*.py
rm -f batch_*.py
rm -f simple_*.py
rm -f minimal_*.py
rm -f complete_*.py
rm -f comprehensive_*.py
rm -f final_*.py
rm -f multi_*.py
rm -f dialect_*.py
rm -f create_simple_db.py
rm -f emergency_db.py
rm -f force_*.py
rm -f nuclear_*.py
rm -f deploy_*.py
rm -f download_*.py
rm -f real_db_sample.py
rm -f cleanup_for_deployment.py
rm -f run_etl.py
rm -f setup_comprehensive_db.py

# Remove documentation files (keep only essential ones)
rm -f CAMEL_*.md
rm -f COMPREHENSIVE_*.md
rm -f DEPLOYMENT_*.md
rm -f FINAL_*.md
rm -f HOW_TO_*.md
rm -f MISSING_*.md
rm -f REQUIREMENTS_*.md
rm -f ULTIMATE_*.py
rm -f DEPLOYMENT_*.py
rm -f FINAL_*.py
rm -f detailed_*.md
rm -f screen_*.md

# Remove build artifacts and cache
rm -rf __pycache__/
rm -rf .venv/
rm -rf app/__pycache__/
rm -rf app/*/__pycache__/

# Remove Docker files (Render uses different deployment)
rm -f Dockerfile
rm -f docker-compose.yml
rm -f build.sh

echo "✅ Cleanup complete - ready for Render!"
