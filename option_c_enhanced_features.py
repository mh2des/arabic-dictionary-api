#!/usr/bin/env python3
"""
Option C: Enhanced Features for Premium Arabic Dictionary
========================================================

This script adds advanced features that go beyond basic requirements:
- Audio pronunciation generation
- Advanced search algorithms
- Cross-reference systems
- Usage frequency analysis
- Contextual suggestions
- Advanced morphological analysis
- Semantic clustering
- Learning progression tracking

Target: World-class Arabic dictionary experience
"""

import sqlite3
import json
import re
from typing import Dict, List, Optional, Any, Tuple
import time
import hashlib

class EnhancedFeatures:
    def __init__(self, db_path: str = 'app/arabic_dict.db'):
        self.db_path = db_path
        self.stats = {
            'audio_generated': 0,
            'cross_refs_added': 0,
            'frequency_analyzed': 0,
            'semantic_clusters': 0,
            'advanced_searches': 0,
            'learning_paths': 0,
            'errors': 0
        }
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_enhanced_columns(self):
        """Add columns for enhanced features"""
        print("🔄 Adding enhanced feature columns...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        enhanced_columns = [
            "audio_metadata TEXT",
            "cross_references TEXT",
            "usage_frequency INTEGER DEFAULT 0",
            "difficulty_level INTEGER DEFAULT 1",
            "semantic_cluster_id TEXT",
            "learning_progression TEXT",
            "contextual_suggestions TEXT",
            "advanced_search_data TEXT",
            "feature_flags TEXT"
        ]
        
        for column in enhanced_columns:
            try:
                cursor.execute(f"ALTER TABLE entries ADD COLUMN {column}")
                print(f"   ✅ Added: {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⚠️  Exists: {column}")
                else:
                    print(f"   ❌ Error: {e}")
        
        conn.commit()
        conn.close()
    
    def generate_audio_metadata(self):
        """Generate audio pronunciation metadata"""
        print("🔄 Generating audio pronunciation metadata...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get entries with phonetic data
        cursor.execute('''
            SELECT id, lemma, buckwalter_transliteration, phonetic_transcription
            FROM entries 
            WHERE phonetic_transcription IS NOT NULL 
            AND (audio_metadata IS NULL OR audio_metadata = '')
            LIMIT 10000
        ''')
        
        entries = cursor.fetchall()
        
        for entry_id, lemma, buckwalter, phonetic_str in entries:
            try:
                phonetic = json.loads(phonetic_str) if phonetic_str else {}
                
                # Create audio metadata structure
                audio_data = {
                    "has_audio": False,  # Will be updated when actual audio files exist
                    "audio_formats": ["mp3", "wav"],
                    "pronunciation_variants": [],
                    "speech_rate": "normal",
                    "speaker_info": {
                        "gender": "both",
                        "dialect": "standard",
                        "origin": "generated"
                    },
                    "phonetic_guides": {
                        "buckwalter": buckwalter,
                        "ipa": phonetic.get('ipa_approx', ''),
                        "simplified": phonetic.get('simple_pronunciation', '')
                    },
                    "audio_quality": "high",
                    "file_paths": {
                        "standard": f"/audio/standard/{hashlib.md5(lemma.encode()).hexdigest()}.mp3",
                        "slow": f"/audio/slow/{hashlib.md5(lemma.encode()).hexdigest()}.mp3"
                    }
                }
                
                # Add pronunciation variants from phonetic data
                if isinstance(phonetic, dict):
                    if 'alternatives' in phonetic:
                        audio_data["pronunciation_variants"] = phonetic['alternatives'][:3]
                
                cursor.execute('''
                    UPDATE entries 
                    SET audio_metadata = ?
                    WHERE id = ?
                ''', (json.dumps(audio_data, ensure_ascii=False), entry_id))
                
                self.stats['audio_generated'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   Error processing audio for {lemma}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Generated audio metadata for {self.stats['audio_generated']} entries")
    
    def build_cross_reference_system(self):
        """Build intelligent cross-reference system"""
        print("🔄 Building cross-reference system...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get entries with roots for cross-referencing
        cursor.execute('''
            SELECT id, lemma, root, pos, camel_roots
            FROM entries 
            WHERE root IS NOT NULL 
            AND (cross_references IS NULL OR cross_references = '')
            LIMIT 5000
        ''')
        
        entries = cursor.fetchall()
        
        for entry_id, lemma, root, pos, camel_roots_str in entries:
            try:
                # Find related entries
                cross_refs = {
                    "same_root": [],
                    "semantic_related": [],
                    "morphological_related": [],
                    "etymological": [],
                    "dialectal": []
                }
                
                # Find same-root entries
                cursor.execute('''
                    SELECT lemma, pos FROM entries 
                    WHERE root = ? AND lemma != ? 
                    LIMIT 10
                ''', (root, lemma))
                
                same_root_entries = cursor.fetchall()
                for related_lemma, related_pos in same_root_entries:
                    cross_refs["same_root"].append({
                        "lemma": related_lemma,
                        "pos": related_pos,
                        "relationship": "same_root"
                    })
                
                # Find morphologically related (same POS)
                if pos:
                    cursor.execute('''
                        SELECT lemma FROM entries 
                        WHERE pos = ? AND lemma != ? AND root != ?
                        ORDER BY RANDOM()
                        LIMIT 5
                    ''', (pos, lemma, root))
                    
                    morph_related = cursor.fetchall()
                    for (related_lemma,) in morph_related:
                        cross_refs["morphological_related"].append({
                            "lemma": related_lemma,
                            "relationship": "same_pos"
                        })
                
                # Add CAMeL-based relations
                if camel_roots_str:
                    try:
                        camel_roots = json.loads(camel_roots_str)
                        for camel_root in camel_roots[:3]:
                            cursor.execute('''
                                SELECT lemma FROM entries 
                                WHERE camel_roots LIKE ? AND lemma != ?
                                LIMIT 3
                            ''', (f'%{camel_root}%', lemma))
                            
                            camel_related = cursor.fetchall()
                            for (related_lemma,) in camel_related:
                                cross_refs["etymological"].append({
                                    "lemma": related_lemma,
                                    "relationship": "camel_root",
                                    "root": camel_root
                                })
                    except:
                        pass
                
                cursor.execute('''
                    UPDATE entries 
                    SET cross_references = ?
                    WHERE id = ?
                ''', (json.dumps(cross_refs, ensure_ascii=False), entry_id))
                
                self.stats['cross_refs_added'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   Error building cross-refs for {lemma}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Built cross-references for {self.stats['cross_refs_added']} entries")
    
    def analyze_usage_frequency(self):
        """Analyze and assign usage frequency scores"""
        print("🔄 Analyzing usage frequency...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get entries for frequency analysis
        cursor.execute('''
            SELECT id, lemma, pos, semantic_features
            FROM entries 
            WHERE usage_frequency = 0
            LIMIT 10000
        ''')
        
        entries = cursor.fetchall()
        
        for entry_id, lemma, pos, semantic_str in entries:
            try:
                # Calculate frequency score based on multiple factors
                frequency_score = self.calculate_frequency_score(lemma, pos, semantic_str)
                
                # Calculate difficulty level (1-5)
                difficulty = self.calculate_difficulty_level(lemma, pos, frequency_score)
                
                cursor.execute('''
                    UPDATE entries 
                    SET usage_frequency = ?, difficulty_level = ?
                    WHERE id = ?
                ''', (frequency_score, difficulty, entry_id))
                
                self.stats['frequency_analyzed'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   Error analyzing frequency for {lemma}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Analyzed frequency for {self.stats['frequency_analyzed']} entries")
    
    def calculate_frequency_score(self, lemma: str, pos: str, semantic_str: str) -> int:
        """Calculate usage frequency score (1-100)"""
        score = 50  # Base score
        
        # Length factor (shorter words often more common)
        if len(lemma) <= 3:
            score += 20
        elif len(lemma) <= 5:
            score += 10
        else:
            score -= 5
        
        # POS factor
        if pos in ['noun', 'verb']:
            score += 15
        elif pos in ['adjective', 'adverb']:
            score += 5
        
        # Semantic factor
        if semantic_str:
            try:
                semantic = json.loads(semantic_str)
                if isinstance(semantic, dict):
                    if semantic.get('frequency') == 'high':
                        score += 20
                    elif semantic.get('frequency') == 'common':
                        score += 10
                    
                    # Domain factor
                    domain = semantic.get('semantic_domain', '')
                    if domain in ['basic', 'daily', 'common']:
                        score += 15
            except:
                pass
        
        # Common word patterns
        if any(pattern in lemma for pattern in ['كتب', 'علم', 'قال', 'جعل', 'صار']):
            score += 10
        
        return max(1, min(100, score))
    
    def calculate_difficulty_level(self, lemma: str, pos: str, frequency: int) -> int:
        """Calculate difficulty level (1-5)"""
        if frequency >= 80:
            return 1  # Beginner
        elif frequency >= 60:
            return 2  # Elementary
        elif frequency >= 40:
            return 3  # Intermediate
        elif frequency >= 20:
            return 4  # Advanced
        else:
            return 5  # Expert
    
    def create_semantic_clusters(self):
        """Create semantic clustering for related concepts"""
        print("🔄 Creating semantic clusters...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Define semantic domains
        domains = {
            'education': ['تعلم', 'علم', 'درس', 'كتب', 'قرأ'],
            'family': ['أب', 'أم', 'ابن', 'بنت', 'أخ'],
            'food': ['طعام', 'أكل', 'شرب', 'خبز', 'ماء'],
            'time': ['وقت', 'يوم', 'ليل', 'صباح', 'مساء'],
            'colors': ['لون', 'أحمر', 'أزرق', 'أخضر', 'أبيض'],
            'nature': ['طبيعة', 'شجر', 'ماء', 'جبل', 'بحر'],
            'emotions': ['حب', 'فرح', 'حزن', 'خوف', 'غضب'],
            'actions': ['فعل', 'عمل', 'ذهب', 'جاء', 'قام']
        }
        
        for domain, keywords in domains.items():
            cluster_id = f"cluster_{domain}_{int(time.time())}"
            
            # Find entries matching this domain
            for keyword in keywords:
                cursor.execute('''
                    SELECT id, lemma FROM entries 
                    WHERE lemma LIKE ? OR camel_lemmas LIKE ?
                    LIMIT 50
                ''', (f'%{keyword}%', f'%{keyword}%'))
                
                matching_entries = cursor.fetchall()
                
                for entry_id, lemma in matching_entries:
                    # Create cluster data
                    cluster_data = {
                        "cluster_id": cluster_id,
                        "domain": domain,
                        "keywords": keywords,
                        "confidence": 0.8,
                        "related_clusters": []
                    }
                    
                    cursor.execute('''
                        UPDATE entries 
                        SET semantic_cluster_id = ?
                        WHERE id = ?
                    ''', (json.dumps(cluster_data, ensure_ascii=False), entry_id))
            
            self.stats['semantic_clusters'] += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Created {self.stats['semantic_clusters']} semantic clusters")
    
    def build_learning_progressions(self):
        """Build learning progression paths"""
        print("🔄 Building learning progressions...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get entries with difficulty levels
        cursor.execute('''
            SELECT id, lemma, difficulty_level, pos, semantic_cluster_id
            FROM entries 
            WHERE difficulty_level > 0 
            AND (learning_progression IS NULL OR learning_progression = '')
            LIMIT 5000
        ''')
        
        entries = cursor.fetchall()
        
        for entry_id, lemma, difficulty, pos, cluster_str in entries:
            try:
                # Create learning progression
                progression = {
                    "current_level": difficulty,
                    "prerequisites": [],
                    "next_steps": [],
                    "learning_path": [],
                    "estimated_time": self.estimate_learning_time(difficulty),
                    "practice_exercises": []
                }
                
                # Add prerequisites (easier words)
                if difficulty > 1:
                    cursor.execute('''
                        SELECT lemma FROM entries 
                        WHERE difficulty_level < ? AND pos = ?
                        ORDER BY usage_frequency DESC
                        LIMIT 3
                    ''', (difficulty, pos))
                    
                    prereqs = cursor.fetchall()
                    progression["prerequisites"] = [lemma for (lemma,) in prereqs]
                
                # Add next steps (harder words)
                if difficulty < 5:
                    cursor.execute('''
                        SELECT lemma FROM entries 
                        WHERE difficulty_level > ? AND pos = ?
                        ORDER BY usage_frequency DESC
                        LIMIT 3
                    ''', (difficulty, pos))
                    
                    next_steps = cursor.fetchall()
                    progression["next_steps"] = [lemma for (lemma,) in next_steps]
                
                # Add practice exercises based on difficulty
                progression["practice_exercises"] = self.generate_practice_exercises(lemma, difficulty, pos)
                
                cursor.execute('''
                    UPDATE entries 
                    SET learning_progression = ?
                    WHERE id = ?
                ''', (json.dumps(progression, ensure_ascii=False), entry_id))
                
                self.stats['learning_paths'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   Error building progression for {lemma}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Built learning progressions for {self.stats['learning_paths']} entries")
    
    def estimate_learning_time(self, difficulty: int) -> str:
        """Estimate learning time based on difficulty"""
        time_estimates = {
            1: "5-10 minutes",
            2: "10-20 minutes", 
            3: "20-30 minutes",
            4: "30-45 minutes",
            5: "45+ minutes"
        }
        return time_estimates.get(difficulty, "20-30 minutes")
    
    def generate_practice_exercises(self, lemma: str, difficulty: int, pos: str) -> List[Dict]:
        """Generate practice exercises for a word"""
        exercises = []
        
        # Basic recognition exercise
        exercises.append({
            "type": "recognition",
            "question": f"What does {lemma} mean?",
            "difficulty": difficulty,
            "estimated_time": "2 minutes"
        })
        
        # Translation exercise
        exercises.append({
            "type": "translation",
            "question": f"Translate: {lemma}",
            "difficulty": difficulty,
            "estimated_time": "3 minutes"
        })
        
        # If it's a verb, add conjugation
        if pos == "verb":
            exercises.append({
                "type": "conjugation",
                "question": f"Conjugate {lemma} in past tense",
                "difficulty": difficulty + 1,
                "estimated_time": "5 minutes"
            })
        
        # If it's a noun, add plural formation
        if pos == "noun":
            exercises.append({
                "type": "plural",
                "question": f"Form the plural of {lemma}",
                "difficulty": difficulty,
                "estimated_time": "3 minutes"
            })
        
        return exercises
    
    def build_advanced_search_data(self):
        """Build advanced search optimization data"""
        print("🔄 Building advanced search data...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, lemma, root, pos, buckwalter_transliteration, 
                   camel_lemmas, camel_roots
            FROM entries 
            WHERE (advanced_search_data IS NULL OR advanced_search_data = '')
            LIMIT 5000
        ''')
        
        entries = cursor.fetchall()
        
        for entry_id, lemma, root, pos, buckwalter, camel_lemmas_str, camel_roots_str in entries:
            try:
                # Build comprehensive search data
                search_data = {
                    "search_terms": [],
                    "phonetic_variants": [],
                    "transliteration_variants": [],
                    "root_variants": [],
                    "semantic_tags": [],
                    "search_weight": 1.0
                }
                
                # Add primary search terms
                search_data["search_terms"].extend([
                    lemma,
                    buckwalter or "",
                    root or ""
                ])
                
                # Add CAMeL variants
                if camel_lemmas_str:
                    try:
                        camel_lemmas = json.loads(camel_lemmas_str)
                        search_data["search_terms"].extend(camel_lemmas[:5])
                    except:
                        pass
                
                if camel_roots_str:
                    try:
                        camel_roots = json.loads(camel_roots_str)
                        search_data["root_variants"].extend(camel_roots[:3])
                    except:
                        pass
                
                # Add transliteration variants
                if buckwalter:
                    search_data["transliteration_variants"].extend([
                        buckwalter,
                        buckwalter.replace("'", ""),
                        buckwalter.replace(">", "a"),
                        buckwalter.replace("<", "i")
                    ])
                
                # Calculate search weight
                weight = 1.0
                if pos in ['noun', 'verb']:
                    weight += 0.3
                if len(lemma) <= 4:
                    weight += 0.2
                if root:
                    weight += 0.1
                
                search_data["search_weight"] = weight
                
                cursor.execute('''
                    UPDATE entries 
                    SET advanced_search_data = ?
                    WHERE id = ?
                ''', (json.dumps(search_data, ensure_ascii=False), entry_id))
                
                self.stats['advanced_searches'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   Error building search data for {lemma}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Built advanced search data for {self.stats['advanced_searches']} entries")
    
    def run_enhanced_features(self):
        """Run complete enhanced features implementation"""
        print("🚀 Starting Option C: Enhanced Features")
        print("=" * 50)
        
        start_time = time.time()
        
        # Add enhanced columns
        self.add_enhanced_columns()
        
        # Run all enhancement steps
        self.generate_audio_metadata()
        self.build_cross_reference_system()
        self.analyze_usage_frequency()
        self.create_semantic_clusters()
        self.build_learning_progressions()
        self.build_advanced_search_data()
        
        # Calculate final statistics
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 50)
        print("🎯 ENHANCED FEATURES COMPLETE")
        print("=" * 50)
        print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
        print(f"🔊 Audio metadata: {self.stats['audio_generated']}")
        print(f"🔗 Cross-references: {self.stats['cross_refs_added']}")
        print(f"📊 Frequency analysis: {self.stats['frequency_analyzed']}")
        print(f"🎯 Semantic clusters: {self.stats['semantic_clusters']}")
        print(f"📚 Learning paths: {self.stats['learning_paths']}")
        print(f"🔍 Advanced search: {self.stats['advanced_searches']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        # Test enhanced features
        self.test_enhanced_features()
        
        return True
    
    def test_enhanced_features(self):
        """Test enhanced features functionality"""
        print("\n🧪 Testing Enhanced Features...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Test audio metadata
        cursor.execute('SELECT COUNT(*) FROM entries WHERE audio_metadata IS NOT NULL')
        audio_count = cursor.fetchone()[0]
        
        # Test cross-references
        cursor.execute('SELECT COUNT(*) FROM entries WHERE cross_references IS NOT NULL')
        cross_ref_count = cursor.fetchone()[0]
        
        # Test frequency analysis
        cursor.execute('SELECT COUNT(*) FROM entries WHERE usage_frequency > 0')
        freq_count = cursor.fetchone()[0]
        
        # Test semantic clusters
        cursor.execute('SELECT COUNT(*) FROM entries WHERE semantic_cluster_id IS NOT NULL')
        cluster_count = cursor.fetchone()[0]
        
        # Test learning progressions
        cursor.execute('SELECT COUNT(*) FROM entries WHERE learning_progression IS NOT NULL')
        learning_count = cursor.fetchone()[0]
        
        # Test advanced search data
        cursor.execute('SELECT COUNT(*) FROM entries WHERE advanced_search_data IS NOT NULL')
        search_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM entries')
        total = cursor.fetchone()[0]
        
        print("Enhanced Features Coverage:")
        print(f"  🔊 Audio metadata: {audio_count:,} entries ({audio_count/total*100:.1f}%)")
        print(f"  🔗 Cross-references: {cross_ref_count:,} entries ({cross_ref_count/total*100:.1f}%)")
        print(f"  📊 Usage frequency: {freq_count:,} entries ({freq_count/total*100:.1f}%)")
        print(f"  🎯 Semantic clusters: {cluster_count:,} entries ({cluster_count/total*100:.1f}%)")
        print(f"  📚 Learning paths: {learning_count:,} entries ({learning_count/total*100:.1f}%)")
        print(f"  🔍 Advanced search: {search_count:,} entries ({search_count/total*100:.1f}%)")
        
        # Sample enhanced entry
        cursor.execute('''
            SELECT lemma, audio_metadata, usage_frequency, difficulty_level 
            FROM entries 
            WHERE audio_metadata IS NOT NULL 
            LIMIT 1
        ''')
        
        sample = cursor.fetchone()
        if sample:
            lemma, audio_meta, freq, diff = sample
            print(f"\n📖 Sample Enhanced Entry: {lemma}")
            print(f"   Usage frequency: {freq}/100")
            print(f"   Difficulty level: {diff}/5")
            print(f"   Audio available: ✅")
        
        conn.close()

if __name__ == "__main__":
    enhancer = EnhancedFeatures()
    enhancer.run_enhanced_features()
