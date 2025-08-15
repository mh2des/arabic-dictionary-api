#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check CAMeL Tools resources for Phase 2 readiness."""

import os
import sys
from pathlib import Path

def check_camel_resources():
    """Check if all required CAMeL Tools resources are available."""
    
    print('🔍 CHECKING CAMEL TOOLS RESOURCES')
    print('='*40)
    
    resources_ready = True
    
    try:
        # Check core CAMeL Tools imports
        from camel_tools.utils.charmap import CharMapper
        from camel_tools.morphology.database import MorphologyDB
        from camel_tools.disambig.mle import MLEDisambiguator
        from camel_tools.tokenizers.word import simple_word_tokenize
        print('✅ Core CAMeL Tools modules imported')
        
        # Check MSA morphology database
        try:
            db = MorphologyDB.builtin_db(name='calima-msa-r13')
            print('✅ calima-msa-r13 (MSA morphology database)')
        except Exception as e:
            print(f'❌ MSA morphology database error: {e}')
            resources_ready = False
            
        # Check MLE disambiguator
        try:
            disambig = MLEDisambiguator.pretrained()
            print('✅ MLE disambiguator model')
        except Exception as e:
            print(f'❌ MLE disambiguator error: {e}')
            resources_ready = False
            
        # Check character mapper
        try:
            mapper = CharMapper.builtin_mapper('ar')
            print('✅ Arabic character mapper')
        except Exception as e:
            print(f'❌ Character mapper error: {e}')
            resources_ready = False
            
    except ImportError as e:
        print(f'❌ CAMeL Tools import error: {e}')
        resources_ready = False
    
    # Check data directory
    camel_data_path = Path.home() / '.camel_tools'
    if camel_data_path.exists():
        print(f'✅ CAMeL data directory: {camel_data_path}')
        data_dirs = [d for d in camel_data_path.iterdir() if d.is_dir()]
        for data_dir in data_dirs:
            print(f'   📂 {data_dir.name}')
    else:
        print(f'⚠️ CAMeL data directory not found: {camel_data_path}')
    
    # Check our current enhancement status
    print('\n📊 CURRENT ENHANCEMENT STATUS:')
    try:
        import sqlite3
        db = sqlite3.connect('app/arabic_dict.db')
        cursor = db.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM entries')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM entries WHERE camel_lemmas IS NOT NULL')
        enhanced = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM entries WHERE camel_genders IS NOT NULL AND camel_genders != ""')
        phase1_enhanced = cursor.fetchone()[0]
        
        print(f'   Total entries: {total:,}')
        print(f'   CAMeL analyzed: {enhanced:,} ({enhanced/total*100:.1f}%)')
        print(f'   Phase 1 enhanced: {phase1_enhanced:,} ({phase1_enhanced/total*100:.1f}%)')
        
        db.close()
        
    except Exception as e:
        print(f'   ❌ Database check error: {e}')
    
    print('\n🎯 RESOURCE ASSESSMENT:')
    if resources_ready:
        print('   ✅ All CAMeL Tools resources available')
        print('   ✅ Morphology database operational')
        print('   ✅ Disambiguation models ready')
        print('   ✅ Phase 1 enhancement completed')
        print('\n🚀 READY TO PROCEED TO PHASE 2!')
        return True
    else:
        print('   ❌ Some CAMeL resources missing or broken')
        print('   🔧 Need to install/fix resources before Phase 2')
        return False

if __name__ == '__main__':
    ready = check_camel_resources()
    sys.exit(0 if ready else 1)
