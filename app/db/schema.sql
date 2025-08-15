-- Database schema for the Arabic dictionary backend
--
-- This SQL file defines the tables required to store lexical
-- entries, their senses, examples, relations and pronunciations.  It
-- also defines an FTS5 virtual table to enable fast full‑text search
-- across lemmas and glosses.

-- Main table of lexical entries.  Each row corresponds to one lemma.
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lemma TEXT NOT NULL,
    lemma_norm TEXT NOT NULL,
    root TEXT,
    pattern TEXT,
    pos TEXT,
    subpos TEXT,
    register TEXT,
    domain TEXT,
    freq_rank INTEGER,
    quality_confidence REAL DEFAULT 0.5,
    quality_reviewed BOOLEAN DEFAULT 0,
    quality_source_count INTEGER DEFAULT 1,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    data JSON NOT NULL  -- full JSON blob for the entry
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_entries_lemma_norm ON entries(lemma_norm);
CREATE INDEX IF NOT EXISTS idx_entries_root ON entries(root);
CREATE INDEX IF NOT EXISTS idx_entries_pos ON entries(pos);
CREATE INDEX IF NOT EXISTS idx_entries_freq_rank ON entries(freq_rank);

-- Table for tracking data sources and provenance
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    license TEXT,
    url TEXT,
    version TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for entry-source relationships
CREATE TABLE IF NOT EXISTS entry_sources (
    entry_id INTEGER,
    source_id INTEGER,
    field_name TEXT,
    confidence REAL DEFAULT 0.5,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
    PRIMARY KEY (entry_id, source_id, field_name)
);

-- Virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    lemma_norm,
    root,
    pattern,
    pos,
    definition,
    meaning,
    content='entries', content_rowid='id'
);

-- Triggers to keep the FTS table in sync with the entries table.
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
  INSERT INTO entries_fts(rowid, lemma_norm, root, pattern, pos, definition, meaning)
  VALUES(
    new.id,
    new.lemma_norm,
    new.root,
    new.pattern,
    new.pos,
    json_extract(new.data, '$.definition'),
    json_extract(new.data, '$.meaning')
  );
END;

CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
  DELETE FROM entries_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
  DELETE FROM entries_fts WHERE rowid = old.id;
  INSERT INTO entries_fts(rowid, lemma_norm, root, pattern, pos, definition, meaning)
  VALUES(
    new.id,
    new.lemma_norm,
    new.root,
    new.pattern,
    new.pos,
    json_extract(new.data, '$.definition'),
    json_extract(new.data, '$.meaning')
  );
END;