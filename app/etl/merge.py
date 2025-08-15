"""
ETL Pipeline and Merge Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module orchestrates the complete ETL pipeline for the Arabic dictionary.
It coordinates data extraction from multiple sources, applies normalization,
resolves conflicts between sources, and merges data into the final database.
"""

from __future__ import annotations

import json
import sqlite3
import os
import csv
from typing import Dict, List, Iterator, Optional, Any, Set, Iterable
from datetime import datetime
from collections import defaultdict

from ..services.normalize import normalize_ar, get_orthographic_variants
from ..models import Entry, Info
from . import arramooz
from .qutrub import extract as extract_qutrub


class ETLPipeline:
    """Manages the complete ETL pipeline for Arabic dictionary data."""
    
    def __init__(self, db_path: str, sources_dir: str):
        """Initialize the ETL pipeline.
        
        Args:
            db_path: Path to the SQLite database
            sources_dir: Path to directory containing source data
        """
        self.db_path = db_path
        self.sources_dir = sources_dir
        self.source_weights = {
            'Arramooz AlWaseet': 0.9,
            'Qutrub': 0.8,
            'Synonyms Dataset': 0.7,
            'Wiktionary': 0.6,
            'Arabic WordNet': 0.8,
            'ArabicOntology': 0.7
        }
        
        # Initialize database schema
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with the required schema."""
        from pathlib import Path
        import sqlite3
        
        # Read schema from file
        schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Create database and apply schema
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.executescript(schema_sql)
                conn.commit()
                print(f"Database schema initialized at: {self.db_path}")
            except Exception as e:
                print(f"Error initializing database schema: {e}")
            finally:
                conn.close()
        else:
            print(f"Warning: Schema file not found at {schema_path}")
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete ETL pipeline.
        
        Returns:
            Dictionary containing pipeline statistics
        """
        print("Starting ETL pipeline...")
        
        # Extract data from all sources
        all_entries = self._extract_all_sources()
        
        # Merge and deduplicate entries  
        merged_entries = self._merge_entries(all_entries)
        
        # Store in database
        self._store_entries(merged_entries)
        
        # Generate statistics
        stats = {
            'total_raw_entries': len(all_entries),
            'total_merged_entries': len(merged_entries),
            'sources_processed': len(set(entry.get('_source', 'Unknown') for entry in all_entries)),
            'pipeline_completed': datetime.now().isoformat()
        }
        
        print(f"ETL pipeline completed: {stats}")
        return stats
    
    def _extract_all_sources(self) -> List[Dict[str, Any]]:
        """Extract data from all available sources.
        
        Returns:
            List of entry dictionaries from all sources
        """
        all_entries = []
        
        # Extract from Arramooz AlWaseet
        arramooz_path = os.path.join(self.sources_dir, 'arramooz-master')
        if os.path.exists(arramooz_path):
            print("Extracting from Arramooz AlWaseet...")
            for entry in arramooz.extract(arramooz_path):
                entry_dict = self._entry_to_dict(entry)
                entry_dict['_source'] = 'Arramooz AlWaseet'
                all_entries.append(entry_dict)
        
        # Extract from Qutrub
        qutrub_path = os.path.join(self.sources_dir, 'qutrub-master')
        if os.path.exists(qutrub_path):
            print("Extracting from Qutrub...")
            for entry in extract_qutrub(qutrub_path):
                entry['_source'] = 'Qutrub'
                all_entries.append(entry)
        
        # Extract from Synonyms dataset
        synonyms_path = os.path.join(self.sources_dir, 'Synonyms-main')
        if os.path.exists(synonyms_path):
            print("Extracting from Synonyms dataset...")
            for entry in self._extract_synonyms(synonyms_path):
                entry['_source'] = 'Synonyms Dataset'
                all_entries.append(entry)
        
        # Extract sample from Wiktionary (limited sample for performance)
        print("Extracting sample from Wiktionary...")
        for entry in self._extract_wiktionary_sample():
            entry['_source'] = 'Wiktionary'
            all_entries.append(entry)
        
        # Extract from HTML files (including Qamoos ul Muheet)
        print("Extracting from HTML files...")
        html_count = 0
        try:
            from .html_extractor import extract_from_html_files
            for entry in extract_from_html_files(self.sources_dir):
                entry_dict = self._entry_to_dict(entry)
                entry_dict['_source'] = 'HTML Dictionary'
                all_entries.append(entry_dict)
                html_count += 1
            print(f"Extracted {html_count} entries from HTML files")
        except ImportError as e:
            print(f"HTML extraction not available: {e}")
        
        # Extract from XML files
        print("Extracting from XML files...")
        xml_count = 0
        try:
            from .xml_extractor import extract_from_xml_files
            for entry in extract_from_xml_files(self.sources_dir):
                entry_dict = self._entry_to_dict(entry)
                entry_dict['_source'] = 'XML Dictionary'
                all_entries.append(entry_dict)
                xml_count += 1
            print(f"Extracted {xml_count} entries from XML files")
        except ImportError as e:
            print(f"XML extraction not available: {e}")
        
        # Extract from SQLite databases
        print("Extracting from SQLite databases...")
        sqlite_count = 0
        try:
            from .sqlite_extractor import extract_from_sqlite_files
            for entry in extract_from_sqlite_files(self.sources_dir):
                entry_dict = self._entry_to_dict(entry)
                entry_dict['_source'] = 'SQLite Database'
                all_entries.append(entry_dict)
                sqlite_count += 1
            print(f"Extracted {sqlite_count} entries from SQLite databases")
        except ImportError as e:
            print(f"SQLite extraction not available: {e}")
        
        # Extract from JSON files
        print("Extracting from JSON files...")
        json_count = 0
        try:
            from .json_extractor import extract_from_json_files
            for entry in extract_from_json_files(self.sources_dir):
                entry_dict = self._entry_to_dict(entry)
                entry_dict['_source'] = 'JSON Dictionary'
                all_entries.append(entry_dict)
                json_count += 1
            print(f"Extracted {json_count} entries from JSON files")
        except ImportError as e:
            print(f"JSON extraction not available: {e}")
        
        # Extract from text files (.dict, .txt, etc.)
        print("Extracting from text files...")
        text_count = 0
        try:
            from .text_extractor import extract_from_text_files
            for entry in extract_from_text_files(self.sources_dir):
                entry_dict = self._entry_to_dict(entry)
                entry_dict['_source'] = 'Text Dictionary'
                all_entries.append(entry_dict)
                text_count += 1
            print(f"Extracted {text_count} entries from text files")
        except ImportError as e:
            print(f"Text extraction not available: {e}")
        
        print(f"Extracted {len(all_entries)} total entries from all sources")
        return all_entries
    
    def _entry_to_dict(self, entry):
        """Convert an entry object to a dictionary if needed."""
        if hasattr(entry, '__dict__'):
            # Convert object to dict, handling special attributes
            entry_dict = {}
            for key, value in entry.__dict__.items():
                if key.startswith('_'):
                    continue
                if hasattr(value, '__dict__'):
                    # Convert nested objects to dicts
                    entry_dict[key] = value.__dict__
                else:
                    entry_dict[key] = value
            return entry_dict
        return entry
    
    def _extract_synonyms(self, synonyms_path: str) -> Iterator[Dict[str, Any]]:
        """Extract data from Synonyms dataset.
        
        Args:
            synonyms_path: Path to the Synonyms dataset directory
            
        Yields:
            Dictionary entries with synonym information
        """
        # Look for various synonym files in the directory
        for root, dirs, files in os.walk(synonyms_path):
            for filename in files:
                if filename.endswith(('.csv', '.txt', '.json')):
                    filepath = os.path.join(root, filename)
                    try:
                        if filename.endswith('.csv'):
                            yield from self._extract_synonyms_csv(filepath)
                        elif filename.endswith('.json'):
                            yield from self._extract_synonyms_json(filepath)
                        elif filename.endswith('.txt'):
                            yield from self._extract_synonyms_txt(filepath)
                    except Exception as e:
                        print(f"Error processing synonyms file {filepath}: {e}")
                        continue
    
    def _extract_synonyms_csv(self, csv_path: str) -> Iterator[Dict[str, Any]]:
        """Extract synonyms from CSV file."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Try to detect if it's a CSV with headers
                sample = f.read(1024)
                f.seek(0)
                
                delimiter = ',' if ',' in sample else '\t'
                reader = csv.reader(f, delimiter=delimiter)
                
                for row in reader:
                    if len(row) >= 2:
                        word = row[0].strip()
                        synonyms = [s.strip() for s in row[1:] if s.strip()]
                        
                        if word and synonyms:
                            yield self._create_synonym_entry(word, synonyms)
        except Exception as e:
            print(f"Error reading CSV synonyms file {csv_path}: {e}")
    
    def _extract_synonyms_json(self, json_path: str) -> Iterator[Dict[str, Any]]:
        """Extract synonyms from JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if isinstance(data, dict):
                    for word, synonyms in data.items():
                        if isinstance(synonyms, list):
                            yield self._create_synonym_entry(word, synonyms)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'word' in item and 'synonyms' in item:
                            yield self._create_synonym_entry(item['word'], item['synonyms'])
        except Exception as e:
            print(f"Error reading JSON synonyms file {json_path}: {e}")
    
    def _extract_synonyms_txt(self, txt_path: str) -> Iterator[Dict[str, Any]]:
        """Extract synonyms from text file."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            word = parts[0].strip()
                            synonyms = [s.strip() for s in parts[1].split(',') if s.strip()]
                            if word and synonyms:
                                yield self._create_synonym_entry(word, synonyms)
        except Exception as e:
            print(f"Error reading text synonyms file {txt_path}: {e}")
    
    def _create_synonym_entry(self, word: str, synonyms: List[str]) -> Dict[str, Any]:
        """Create a dictionary entry for a word with its synonyms."""
        from ..services.normalize import normalize_ar
        from datetime import datetime
        
        lemma_norm = normalize_ar(word)
        return {
            'info': {
                'lemma': word,
                'lemma_norm': lemma_norm,
                'pos': ['unknown'],
                'quality': {
                    'confidence': 0.7,
                    'reviewed': False,
                    'source_count': 1
                },
                'updated_at': datetime.now().isoformat()
            },
            'senses': [{
                'id': f"{lemma_norm}_syn_1",
                'synonyms_ar': synonyms,
                'confidence': 0.7
            }],
            'examples': [],
            'relations': {},
            'pronunciation': {},
            'dialects': [],
            'inflection': {},
            'derivations': {},
            'sources': [{
                'name': 'Synonyms Dataset',
                'license': 'Unknown',
                'url': 'https://github.com/mohataher/Synonyms'
            }]
        }
    
    def _extract_wiktionary_sample(self) -> Iterator[Dict[str, Any]]:
        """Extract a small sample from Wiktionary for demonstration.
        
        Yields:
            Dictionary entries from Wiktionary sample data
        """
        # Sample Wiktionary entries for demonstration
        sample_entries = [
            {
                'word': 'كتاب',
                'definition': 'a written work; book',
                'pos': 'noun',
                'root': 'كتب'
            },
            {
                'word': 'قلم',
                'definition': 'pen, pencil',
                'pos': 'noun', 
                'root': 'قلم'
            },
            {
                'word': 'بيت',
                'definition': 'house, home',
                'pos': 'noun',
                'root': 'بيت'
            }
        ]
        
        from ..services.normalize import normalize_ar
        from datetime import datetime
        
        for sample in sample_entries:
            word = sample['word']
            lemma_norm = normalize_ar(word)
            
            yield {
                'info': {
                    'lemma': word,
                    'lemma_norm': lemma_norm,
                    'root': sample.get('root'),
                    'pos': [sample.get('pos', 'unknown')],
                    'quality': {
                        'confidence': 0.6,
                        'reviewed': False,
                        'source_count': 1
                    },
                    'updated_at': datetime.now().isoformat()
                },
                'senses': [{
                    'id': f"{lemma_norm}_wikt_1",
                    'gloss_en': sample.get('definition'),
                    'confidence': 0.6
                }],
                'examples': [],
                'relations': {},
                'pronunciation': {},
                'dialects': [],
                'inflection': {},
                'derivations': {},
                'sources': [{
                    'name': 'Wiktionary',
                    'license': 'CC BY-SA',
                    'url': 'https://en.wiktionary.org/'
                }]
            }
    
    def _entry_to_dict(self, entry: Entry) -> Dict[str, Any]:
        """Convert Entry object to dictionary."""
        if hasattr(entry, 'data') and entry.data:
            return json.loads(entry.data)
        else:
            # Convert pydantic model to dict
            return {
                'info': entry.info.dict() if entry.info else {},
                'senses': [s.dict() for s in entry.senses] if entry.senses else [],
                'examples': [e.dict() for e in entry.examples] if entry.examples else [],
                'relations': entry.relations.dict() if entry.relations else {},
                'pronunciation': entry.pronunciation.dict() if entry.pronunciation else {},
                'dialects': [d.dict() for d in entry.dialects] if entry.dialects else [],
                'inflection': entry.inflection.dict() if entry.inflection else {},
                'derivations': entry.derivations.dict() if entry.derivations else {},
                'sources': []
            }
    
    def _merge_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge entries with the same lemma."""
        print("Merging and deduplicating entries...")
        
        # Group entries by normalized lemma
        lemma_groups = defaultdict(list)
        for entry in entries:
            info = entry.get('info', {})
            lemma_norm = info.get('lemma_norm', '')
            if lemma_norm:
                lemma_groups[lemma_norm].append(entry)
        
        merged_entries = []
        for lemma_norm, group in lemma_groups.items():
            if len(group) == 1:
                # Single entry, no merging needed
                merged_entries.append(group[0])
            else:
                # Multiple entries, merge them
                merged = self._merge_entry_group(group)
                merged_entries.append(merged)
        
        print(f"Merged {len(entries)} entries into {len(merged_entries)} unique entries")
        return merged_entries
    
    def _merge_entry_group(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge a group of entries for the same lemma."""
        # Use the highest quality entry as base
        base_entry = max(group, key=lambda e: e.get('info', {}).get('quality', {}).get('confidence', 0))
        
        # Merge senses from all entries
        all_senses = []
        for entry in group:
            all_senses.extend(entry.get('senses', []))
        
        # Merge sources
        all_sources = []
        for entry in group:
            all_sources.extend(entry.get('sources', []))
            source_name = entry.get('_source')
            if source_name and source_name not in [s.get('name') for s in all_sources]:
                all_sources.append({'name': source_name})
        
        # Create merged entry
        merged = base_entry.copy()
        merged['senses'] = all_senses
        merged['sources'] = all_sources
        
        # Update quality metadata
        if 'info' in merged and 'quality' in merged['info']:
            merged['info']['quality']['source_count'] = len(all_sources)
            # Average confidence across sources
            confidences = [e.get('info', {}).get('quality', {}).get('confidence', 0) for e in group]
            if confidences:
                merged['info']['quality']['confidence'] = sum(confidences) / len(confidences)
        
        return merged
    
    def _store_entries(self, entries: List[Dict[str, Any]]) -> None:
        """Store entries in the database."""
        print(f"Storing {len(entries)} entries in database...")
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Clear existing entries 
            cursor.execute("DELETE FROM entries")
            
            for entry in entries:
                info = entry.get('info', {})
                lemma = info.get('lemma', '')
                lemma_norm = info.get('lemma_norm', '')
                pos = ','.join(info.get('pos', []))
                root = info.get('root', '')
                
                # Serialize full entry data
                entry_data = json.dumps(entry, ensure_ascii=False)
                
                cursor.execute("""
                    INSERT INTO entries (lemma, lemma_norm, pos, root, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (lemma, lemma_norm, pos, root, entry_data))
            
            conn.commit()
            print(f"Successfully stored {len(entries)} entries")
            
        except Exception as e:
            print(f"Error storing entries: {e}")
            conn.rollback()
        finally:
            conn.close()


def run_etl_pipeline(db_path: str, sources_dir: str) -> Dict[str, Any]:
    """Run the complete ETL pipeline.
    
    Args:
        db_path: Path to the SQLite database file
        sources_dir: Path to directory containing source data
        
    Returns:
        Dictionary containing pipeline statistics
    """
    pipeline = ETLPipeline(db_path, sources_dir)
    return pipeline.run_full_pipeline()


def merge(sources: Dict[str, Iterable[Entry]]) -> List[Entry]:
    """Merge entries from multiple sources into unified entries.

    Args:
        sources: Mapping of source name to iterable of Entry objects.

    Returns:
        List of merged Entry objects with conflicts resolved.
    """
    # Group entries by normalized lemma
    lemma_groups = defaultdict(list)
    
    for source_name, entries in sources.items():
        for entry in entries:
            if entry.info and entry.info.lemma_norm:
                lemma_groups[entry.info.lemma_norm].append((source_name, entry))
    
    merged_entries = []
    
    for lemma_norm, group in lemma_groups.items():
        if len(group) == 1:
            # Only one entry, keep as-is
            _, entry = group[0]
            merged_entries.append(entry)
        else:
            # Multiple entries, need to merge
            merged = _merge_entry_group(group)
            merged_entries.append(merged)
    
    return merged_entries


def _merge_entry_group(group: List[tuple[str, Entry]]) -> Entry:
    """Merge multiple entries for the same lemma into a single entry."""
    # Sort by source reliability (you can customize this)
    source_priority = {
        'Arramooz AlWaseet': 1,
        'Qutrub': 2, 
        'Arabic WordNet': 3,
        'Wiktionary': 4,
        'Synonyms': 5
    }
    
    group.sort(key=lambda x: source_priority.get(x[0], 999))
    
    # Use the highest priority entry as base
    base_source, base_entry = group[0]
    
    # Collect additional data from other sources
    all_senses = list(base_entry.senses) if base_entry.senses else []
    all_examples = list(base_entry.examples) if base_entry.examples else []
    
    for source_name, entry in group[1:]:
        if entry.senses:
            all_senses.extend(entry.senses)
        if entry.examples:
            all_examples.extend(entry.examples)
    
    # Create merged entry
    merged = Entry(
        info=base_entry.info,
        senses=all_senses,
        examples=all_examples,
        relations=base_entry.relations,
        pronunciation=base_entry.pronunciation,
        dialects=base_entry.dialects,
        inflection=base_entry.inflection,
        derivations=base_entry.derivations
    )
    
    return merged
