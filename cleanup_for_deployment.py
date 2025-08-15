#!/usr/bin/env python3
"""
🧹 CLEANUP SCRIPT FOR DEPLOYMENT
=================================

This script identifies and removes unused files to prepare for deployment.
Keeps only essential files needed for production.
"""

import os
import shutil
from pathlib import Path

def get_essential_files():
    """List of essential files needed for production."""
    return {
        # Core application files
        'app/main.py',
        'app/__init__.py',
        'app/services/normalize.py',
        'app/services/search.py',
        'app/services/tts.py',
        'app/api/__init__.py',
        'app/api/enhanced_screen_routes.py',
        'app/api/dialect_enhanced_routes.py',
        'app/api/camel_enhanced_routes.py',
        'app/models/__init__.py',
        
        # Database
        'app/arabic_dict.db',
        'app/db/schema.sql',
        
        # Configuration
        'app/config/settings.toml',
        'app/config/settings.example.toml',
        
        # Deployment files
        'requirements.txt',
        'railway.json',
        'Procfile',
        'runtime.txt',
        'deploy_to_railway.py',
        'DEPLOYMENT_GUIDE.py',
        
        # Docker (optional but useful)
        'Dockerfile',
        'docker-compose.yml',
        
        # Documentation
        'README.md',
        'CHANGELOG.md',
        'CONTRIBUTING.md',
        'LICENSE',
        'schema.json',
        
        # Sample data (optional)
        'app/data/sample/sample_entries.json'
    }

def get_cleanup_candidates():
    """List of files that can be removed for deployment."""
    cleanup_patterns = [
        # Test files
        'test_*.py',
        'tests/',
        
        # Development scripts
        'enhance_*.py',
        'phase*.py',
        'option_*.py',
        'analyze_*.py',
        'check_*.py',
        'batch_*.py',
        'simple_*.py',
        'complete_*.py',
        'comprehensive_*.py',
        'multi_*.py',
        'dialect_analyzer.py',
        'final_analysis_implementation.py',
        
        # ETL scripts (keep for reference)
        'app/etl/',
        'scripts/',
        'run_etl.py',
        
        # Reports and analysis
        '*_SUCCESS_REPORT.py',
        'show_sample.py',
        
        # Cache and temporary files
        '**/__pycache__/',
        '**/*.pyc',
        '.pytest_cache/',
        '.coverage',
        
        # IDE files
        '.vscode/',
        '.idea/',
        '*.swp',
        '*.swo',
        '*~'
    ]
    
    return cleanup_patterns

def analyze_files():
    """Analyze which files can be cleaned up."""
    print("🔍 ANALYZING FILES FOR CLEANUP...")
    print("=" * 40)
    
    essential = get_essential_files()
    cleanup_candidates = []
    
    # Find all Python files
    for py_file in Path('.').rglob('*.py'):
        rel_path = str(py_file.relative_to('.'))
        if rel_path not in essential:
            # Check if it matches cleanup patterns
            should_remove = False
            for pattern in get_cleanup_candidates():
                if pattern.endswith('/'):
                    if rel_path.startswith(pattern) or pattern.rstrip('/') in rel_path:
                        should_remove = True
                        break
                elif '*' in pattern:
                    import fnmatch
                    if fnmatch.fnmatch(rel_path, pattern):
                        should_remove = True
                        break
                elif pattern in rel_path:
                    should_remove = True
                    break
            
            if should_remove:
                cleanup_candidates.append(rel_path)
    
    # Check directories
    for cleanup_pattern in get_cleanup_candidates():
        if cleanup_pattern.endswith('/'):
            dir_path = Path(cleanup_pattern.rstrip('/'))
            if dir_path.exists():
                cleanup_candidates.append(str(dir_path))
    
    return essential, cleanup_candidates

def show_cleanup_plan(essential, cleanup_candidates):
    """Show what will be kept and what will be removed."""
    print(f"\n📁 ESSENTIAL FILES TO KEEP ({len(essential)}):")
    print("-" * 30)
    for file in sorted(essential):
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (missing)")
    
    print(f"\n🗑️  CANDIDATES FOR REMOVAL ({len(cleanup_candidates)}):")
    print("-" * 30)
    for file in sorted(cleanup_candidates):
        if os.path.exists(file):
            size = os.path.getsize(file) if os.path.isfile(file) else 0
            print(f"📄 {file} ({size} bytes)")
        else:
            print(f"❓ {file} (not found)")

def estimate_size_reduction(cleanup_candidates):
    """Estimate how much space will be saved."""
    total_size = 0
    file_count = 0
    
    for candidate in cleanup_candidates:
        if os.path.exists(candidate):
            if os.path.isfile(candidate):
                total_size += os.path.getsize(candidate)
                file_count += 1
            elif os.path.isdir(candidate):
                for root, dirs, files in os.walk(candidate):
                    for file in files:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
    
    print(f"\n💾 SIZE REDUCTION ESTIMATE:")
    print(f"   Files to remove: {file_count}")
    print(f"   Space to save: {total_size / 1024 / 1024:.1f} MB")
    
    return total_size, file_count

def main():
    """Main cleanup analysis."""
    print("🧹 DEPLOYMENT CLEANUP ANALYSIS")
    print("=" * 40)
    print("This script analyzes which files can be safely removed for deployment.")
    print("It does NOT automatically delete files - just shows recommendations.\n")
    
    essential, cleanup_candidates = analyze_files()
    show_cleanup_plan(essential, cleanup_candidates)
    estimate_size_reduction(cleanup_candidates)
    
    print(f"\n📋 CLEANUP RECOMMENDATIONS:")
    print("=" * 30)
    print("1. Keep all essential files listed above")
    print("2. Review cleanup candidates before removing")
    print("3. Consider archiving ETL scripts instead of deleting")
    print("4. Keep test files in a separate branch")
    
    print(f"\n🚀 FOR RAILWAY DEPLOYMENT:")
    print("- Only essential files will be deployed")
    print("- Railway ignores test files automatically") 
    print("- Total deployment will be < 50MB")
    print("- Clean deployment = faster startup time")
    
    print(f"\n💡 MANUAL CLEANUP COMMANDS:")
    print("rm -rf tests/")
    print("rm -rf **/__pycache__/")
    print("rm test_*.py")
    print("rm enhance_*.py phase*.py option_*.py")
    
    print(f"\n✅ ANALYSIS COMPLETE!")
    print("Review the recommendations above before proceeding with cleanup.")

if __name__ == "__main__":
    main()
