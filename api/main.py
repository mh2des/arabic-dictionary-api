# FastAPI for Arabic Dictionary using SQLite (fallback) or Postgres if DB_DSN is set.
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from typing import Optional
import os, json, sqlite3, datetime, hashlib
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util_normalize import aggressive_normalize as norm
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import psycopg2  # optional
except Exception:
    psycopg2 = None

DB_DSN = os.getenv("DB_DSN")
SQLITE_DB = os.getenv("SQLITE_DB", "dict.db")

app = FastAPI(title="Arabic Dictionary API", version="0.3.0", default_response_class=ORJSONResponse)

# CORS for Flutter/web clients
allow_origins = os.getenv("ALLOW_ORIGINS", "*")
origins = [o.strip() for o in allow_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_sqlite():
    return bool(SQLITE_DB) and not DB_DSN

def conn_pg():
    if not psycopg2:
        raise HTTPException(500, "psycopg2 not installed; set SQLITE_DB or install requirements")
    return psycopg2.connect(DB_DSN)

def conn_sqlite():
    return sqlite3.connect(SQLITE_DB)

@app.get("/health")
def health():
    return {"ok": True, "backend": "sqlite" if is_sqlite() else "postgres"}

@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "Arabic Dictionary API",
        "version": "1.0.0",
        "description": "Comprehensive Arabic dictionary with dialect support",
        "features": [
            "74,977 Arabic entries",
            "10 dialect support",
            "Smart search & autocomplete", 
            "Root exploration",
            "Semantic networks",
            "Learning discovery"
        ],
        "docs": "/docs",
        "stats": "/stats",
        "health": "/health"
    }

@app.get("/version")
def version():
    return {"version": "0.3.0", "backend": "sqlite" if is_sqlite() else "postgres"}

@app.get("/metrics")
def metrics():
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT COUNT(*) FROM entries")
            entries_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM senses")
            senses_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM translations")
            translations_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM inflections")
            inflections_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM synsets")
            synsets_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM entry_synsets")
            entry_synsets_count = cur.fetchone()[0]
            try:
                cur.execute("SELECT COUNT(*) FROM relations")
                relations_count = cur.fetchone()[0]
            except:
                relations_count = 0
            try:
                cur.execute("SELECT COUNT(*) FROM dialects")
                dialects_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM dialect_words")
                dialect_words_count = cur.fetchone()[0]
            except:
                dialects_count = 0
                dialect_words_count = 0
        return {
            "entries": entries_count,
            "senses": senses_count,
            "translations": translations_count,
            "inflections": inflections_count,
            "synsets": synsets_count,
            "entry_synsets": entry_synsets_count,
            "relations": relations_count,
            "dialects": dialects_count,
            "dialect_words": dialect_words_count,
            "backend": "sqlite"
        }
    return {"backend": "postgres", "message": "metrics not implemented for postgres"}

@app.get("/lookup")
def lookup(q: str = Query(..., min_length=1), limit: int = 20):
    nq = norm(q)
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT id, lemma_surface, pos FROM entries WHERE lemma_norm=? LIMIT ?", (nq, limit))
            rows = cur.fetchall()
            if len(rows) < limit:
                need = limit - len(rows)
                # Use rowid join with content table
                cur.execute("SELECT rowid FROM entries_fts WHERE entries_fts MATCH ? LIMIT ?", (nq + '*', need))
                seen_ids = {r[0] for r in rows}
                rowids = [rid for (rid,) in cur.fetchall()]
                if rowids:
                    qmarks = ','.join(['?'] * len(rowids))
                    cur.execute(f"SELECT id, lemma_surface, pos FROM entries WHERE rowid IN ({qmarks})", rowids)
                    for r in cur.fetchall():
                        if r[0] in seen_ids: continue
                        rows.append(r)
        return [{"id": r[0], "lemma": r[1], "pos": r[2]} for r in rows]
    else:
        sql = """
        WITH hits AS (
          SELECT e.id, e.lemma_surface, e.pos, 1.0 FROM entries e WHERE e.lemma_norm = %s
          UNION ALL
          SELECT e.id, e.lemma_surface, e.pos, similarity(e.lemma_norm, %s) FROM entries e WHERE e.lemma_norm % %s
          UNION ALL
          SELECT e.id, e.lemma_surface, e.pos, 0.85 FROM inflections i JOIN entries e ON e.id=i.entry_id WHERE i.form_norm = %s
          UNION ALL
          SELECT e.id, e.lemma_surface, e.pos, similarity(i.form_norm, %s) FROM inflections i JOIN entries e ON e.id=i.entry_id WHERE i.form_norm % %s
        ) SELECT id, lemma_surface, pos FROM hits ORDER BY 4 DESC LIMIT %s;
        """
        with conn_pg() as c:
            with c.cursor() as cur:
                cur.execute(sql, (nq, nq, nq, nq, nq, nq, limit))
                rows = cur.fetchall()
        return [{"id": r[0], "lemma": r[1], "pos": r[2]} for r in rows]

@app.get("/entry/{entry_id}")
def get_entry(entry_id: str):
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT id, lemma_surface, lemma_norm, pos, root, etymology FROM entries WHERE id=?", (entry_id,))
            ent = cur.fetchone()
            if not ent:
                raise HTTPException(404, "Entry not found")
            cur.execute("SELECT sense_id, gloss_ar, gloss_en, examples FROM senses WHERE entry_id=?", (entry_id,))
            senses = []
            for s in cur.fetchall():
                ex = s[3]
                senses.append({"sense_id": s[0], "gloss_ar": s[1], "gloss_en": s[2], "examples": json.loads(ex) if ex else []})
            cur.execute("SELECT form_surface, features FROM inflections WHERE entry_id=?", (entry_id,))
            infl = []
            for r in cur.fetchall():
                infl.append({"form": r[0], "features": json.loads(r[1]) if r[1] else {}})
            cur.execute("SELECT sense_id, lang, text FROM translations WHERE sense_id IN (SELECT sense_id FROM senses WHERE entry_id=?)", (entry_id,))
            trans = [{"sense_id": r[0], "lang": r[1], "text": r[2]} for r in cur.fetchall()]
            # relations per sense (with fallback if schema column is missing)
            try:
                cur.execute("SELECT sense_id, type, target, target_lang, target_entry_id FROM relations WHERE sense_id IN (SELECT sense_id FROM senses WHERE entry_id=?)", (entry_id,))
                rels = [{"sense_id": r[0], "type": r[1], "target": r[2], "target_lang": r[3], "target_entry_id": r[4]} for r in cur.fetchall()]
            except sqlite3.OperationalError:
                cur.execute("SELECT sense_id, type, target, target_lang FROM relations WHERE sense_id IN (SELECT sense_id FROM senses WHERE entry_id=?)", (entry_id,))
                rels = [{"sense_id": r[0], "type": r[1], "target": r[2], "target_lang": r[3], "target_entry_id": None} for r in cur.fetchall()]
        # reshape relations per sense for nicer card consumption
        rel_map = {}
        for r in rels:
            rel_map.setdefault(r["sense_id"], {}).setdefault(r["type"], []).append({"target": r["target"], "lang": r["target_lang"], "entry_id": r.get("target_entry_id")})
        # attach relations to senses
        senses_out = []
        for s in senses:
            rmap = rel_map.get(s["sense_id"], {})
            senses_out.append({**s, "relations": rmap})
        return {"id": ent[0], "lemma": ent[1], "lemma_norm": ent[2], "pos": ent[3], "root": ent[4], "etymology": ent[5], "senses": senses_out, "inflections": infl, "translations": trans}
    else:
        with conn_pg() as c:
            with c.cursor() as cur:
                cur.execute("SELECT id, lemma_surface, lemma_norm, pos, root, etymology FROM entries WHERE id=%s", (entry_id,))
                ent = cur.fetchone()
                if not ent:
                    raise HTTPException(404, "Entry not found")
                cur.execute("SELECT sense_id, gloss_ar, gloss_en, examples FROM senses WHERE entry_id=%s", (entry_id,))
                senses = []
                for s in cur.fetchall():
                    senses.append({"sense_id": s[0], "gloss_ar": s[1], "gloss_en": s[2], "examples": s[3]})
                cur.execute("SELECT form_surface, features FROM inflections WHERE entry_id=%s", (entry_id,))
                infl = [{"form": r[0], "features": r[1]} for r in cur.fetchall()]
                cur.execute("SELECT sense_id, lang, text FROM translations t WHERE t.sense_id IN (SELECT sense_id FROM senses WHERE entry_id=%s)", (entry_id,))
                trans = [{"sense_id": r[0], "lang": r[1], "text": r[2]} for r in cur.fetchall()]
        return {"id": ent[0], "lemma": ent[1], "lemma_norm": ent[2], "pos": ent[3], "root": ent[4], "etymology": ent[5], "senses": senses, "inflections": infl, "translations": trans}

@app.get("/forms/{form}")
def form_lookup(form: str):
    nq = norm(form)
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT DISTINCT e.id, e.lemma_surface, e.pos FROM inflections i JOIN entries e ON e.id=i.entry_id WHERE i.form_norm=? LIMIT 30", (nq,))
            rows = cur.fetchall()
            if len(rows) < 30:
                need = 30 - len(rows)
                cur.execute("SELECT rowid FROM inflections_fts WHERE inflections_fts MATCH ? LIMIT ?", (nq + '*', need))
                rid_list = [r[0] for r in cur.fetchall()]
                if rid_list:
                    qmarks = ','.join(['?'] * len(rid_list))
                    cur.execute(f"SELECT DISTINCT e.id, e.lemma_surface, e.pos FROM inflections i JOIN entries e ON e.id=i.entry_id WHERE i.rowid IN ({qmarks})", rid_list)
                    add = cur.fetchall()
                    # merge with existing without duplicates
                    seen = {(r[0], r[1], r[2]) for r in rows}
                    for r in add:
                        if r in seen: continue
                        rows.append(r)
        return [{"id": r[0], "lemma": r[1], "pos": r[2]} for r in rows]
    else:
        return []

@app.get("/browse/pos/{pos}")
def browse_by_pos(pos: str, q: Optional[str] = None, limit: int = 100, offset: int = 0):
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            if q:
                nq = norm(q) + '*'
                # intersect FTS with POS
                cur.execute(
                    "SELECT e.id, e.lemma_surface, e.pos FROM entries e "
                    "JOIN entries_fts f ON f.rowid = e.rowid "
                    "WHERE e.pos = ? AND entries_fts MATCH ? "
                    "LIMIT ? OFFSET ?",
                    (pos, nq, limit, offset)
                )
            else:
                cur.execute("SELECT id, lemma_surface, pos FROM entries WHERE pos=? ORDER BY lemma_surface LIMIT ? OFFSET ?", (pos, limit, offset))
            rows = cur.fetchall()
        return [{"id": r[0], "lemma": r[1], "pos": r[2]} for r in rows]
    return []

@app.get("/search_meaning")
@app.get("/meanings")
def search_meaning(q: str, lang: Optional[str] = None, limit: int = 30):
    term = (q or '').strip()
    if not term:
        raise HTTPException(400, "q is required")
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            try:
                # FTS over glosses
                cur.execute(
                    "SELECT s.entry_id FROM senses s JOIN senses_fts f ON f.rowid = s.rowid WHERE senses_fts MATCH ? LIMIT ?",
                    (term + '*', limit * 5)
                )
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                # Fallback: LIKE on gloss fields
                like = f"%{term}%"
                if lang == 'en':
                    cur.execute("SELECT entry_id FROM senses WHERE gloss_en LIKE ? LIMIT ?", (like, limit * 5))
                elif lang == 'ar':
                    cur.execute("SELECT entry_id FROM senses WHERE gloss_ar LIKE ? LIMIT ?", (like, limit * 5))
                else:
                    cur.execute("SELECT entry_id FROM senses WHERE gloss_en LIKE ? OR gloss_ar LIKE ? LIMIT ?", (like, like, limit * 5))
                rows = cur.fetchall()
            # Distinct entry ids
            eids, seen = [], set()
            for (eid,) in rows:
                if eid in seen: continue
                seen.add(eid)
                eids.append(eid)
            if not eids:
                return []
            qmarks = ','.join(['?'] * min(len(eids), limit))
            cur.execute(f"SELECT id, lemma_surface, pos FROM entries WHERE id IN ({qmarks}) LIMIT ?", [*eids[:limit], limit])
            return [{"id": r[0], "lemma": r[1], "pos": r[2]} for r in cur.fetchall()]
    return []

@app.get("/relations")
@app.get("/synonyms")
def get_relations(entry_id: str, type: Optional[str] = None, limit: int = 100):
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            try:
                if type:
                    cur.execute("SELECT r.type, r.target, r.target_lang FROM relations r WHERE r.sense_id IN (SELECT sense_id FROM senses WHERE entry_id=?) AND r.type=? LIMIT ?", (entry_id, type, limit))
                else:
                    cur.execute("SELECT r.type, r.target, r.target_lang FROM relations r WHERE r.sense_id IN (SELECT sense_id FROM senses WHERE entry_id=?) LIMIT ?", (entry_id, limit))
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                rows = []
        return [{"type": r[0], "target": r[1], "target_lang": r[2]} for r in rows]
    return []

@app.get("/suggest")
@app.get("/autocomplete")
def suggest(q: str, limit: int = 10):
    nq = norm(q)
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            suggestions = []
            
            # Try prefix match first (most relevant)
            cur.execute("SELECT DISTINCT lemma_surface FROM entries WHERE lemma_norm LIKE ? ORDER BY LENGTH(lemma_surface), lemma_surface LIMIT ?", (nq + '%', limit))
            prefix_results = [r[0] for r in cur.fetchall()]
            suggestions.extend(prefix_results)
            
            # If we need more, try FTS
            if len(suggestions) < limit:
                try:
                    need_more = limit - len(suggestions)
                    cur.execute("SELECT rowid FROM entries_fts WHERE entries_fts MATCH ? LIMIT ?", (nq + '*', need_more * 2))
                    rowids = [r[0] for r in cur.fetchall()]
                    if rowids:
                        qmarks = ','.join(['?'] * len(rowids))
                        cur.execute(f"SELECT DISTINCT lemma_surface FROM entries WHERE rowid IN ({qmarks}) ORDER BY LENGTH(lemma_surface), lemma_surface", rowids)
                        fts_results = [r[0] for r in cur.fetchall()]
                        # Add new suggestions not already in list
                        for suggestion in fts_results:
                            if suggestion not in suggestions:
                                suggestions.append(suggestion)
                                if len(suggestions) >= limit:
                                    break
                except sqlite3.OperationalError:
                    pass  # FTS not available
            
            return suggestions[:limit]
    else:
        return []

@app.get("/reverse")
def reverse_lookup(q: str, lang: Optional[str] = None, limit: int = 30):
    nq = (q or '').strip()
    if not nq:
        raise HTTPException(400, "q is required")
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            
            # Try exact match first
            if lang:
                cur.execute("SELECT DISTINCT sense_id FROM translations WHERE lang = ? AND LOWER(text) = LOWER(?)", (lang, nq))
            else:
                cur.execute("SELECT DISTINCT sense_id FROM translations WHERE LOWER(text) = LOWER(?)", (nq,))
            
            exact_sids = [r[0] for r in cur.fetchall()]
            
            # Try LIKE pattern match for partial matches
            like_pattern = f"%{nq}%"
            if lang:
                cur.execute("SELECT DISTINCT sense_id FROM translations WHERE lang = ? AND LOWER(text) LIKE LOWER(?) LIMIT ?", (lang, like_pattern, limit * 2))
            else:
                cur.execute("SELECT DISTINCT sense_id FROM translations WHERE LOWER(text) LIKE LOWER(?) LIMIT ?", (like_pattern, limit * 2))
            
            like_sids = [r[0] for r in cur.fetchall()]
            
            # Combine exact matches first, then LIKE matches
            all_sids = exact_sids + [sid for sid in like_sids if sid not in exact_sids]
            
            # Try FTS if we still don't have enough results
            if len(all_sids) < limit:
                try:
                    cur.execute("SELECT rowid FROM translations_fts WHERE translations_fts MATCH ? LIMIT ?", (nq + '*', limit))
                    fts_rowids = [r[0] for r in cur.fetchall()]
                    if fts_rowids:
                        qmarks = ','.join(['?'] * len(fts_rowids))
                        if lang:
                            cur.execute(f"SELECT DISTINCT sense_id FROM translations WHERE lang = ? AND rowid IN ({qmarks})", [lang] + fts_rowids)
                        else:
                            cur.execute(f"SELECT sense_id FROM translations WHERE rowid IN ({qmarks})", fts_rowids)
                        fts_sids = [r[0] for r in cur.fetchall()]
                        all_sids.extend([sid for sid in fts_sids if sid not in all_sids])
                except sqlite3.OperationalError:
                    pass  # FTS not available
            
            # Get entry information for found senses
            out = []
            seen_entries = set()
            for sid in all_sids[:limit * 2]:  # Get more to deduplicate
                cur.execute("SELECT e.id, e.lemma_surface, e.pos FROM senses s JOIN entries e ON e.id=s.entry_id WHERE s.sense_id=?", (sid,))
                r = cur.fetchone()
                if r and r[0] not in seen_entries:
                    seen_entries.add(r[0])
                    out.append({"id": r[0], "lemma": r[1], "pos": r[2]})
                    if len(out) >= limit:
                        break
            
            return out
    else:
        return []

@app.get("/by_root")
def by_root(root: str, limit: int = 100):
    r = norm(root).replace('-', '')
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT id, lemma_surface, pos FROM entries WHERE replace(coalesce(root,''), '-', '') = ? ORDER BY lemma_surface LIMIT ?", (r, limit))
            rows = cur.fetchall()
            if not rows:
                # Fallback: pattern match letters in order on lemma_norm (very rough root search)
                pat = '%' + '%'.join(list(r)) + '%'
                cur.execute("SELECT id, lemma_surface, pos FROM entries WHERE lemma_norm LIKE ? ESCAPE '\\' ORDER BY LENGTH(lemma_norm), lemma_surface LIMIT ?", (pat, limit))
                rows = cur.fetchall()
        return [{"id": x[0], "lemma": x[1], "pos": x[2]} for x in rows]
    else:
        return []

@app.get("/random")
def random_entry():
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT id, lemma_surface, pos FROM entries ORDER BY RANDOM() LIMIT 1")
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "No entries")
            return {"id": r[0], "lemma": r[1], "pos": r[2]}
    return {}

@app.get("/word_of_the_day")
def word_of_the_day():
    if is_sqlite():
        today = datetime.date.today().isoformat()
        h = int(hashlib.sha1(today.encode()).hexdigest()[:8], 16)
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT COUNT(*) FROM entries")
            total = cur.fetchone()[0] or 1
            offset = h % total
            cur.execute("SELECT id, lemma_surface, pos FROM entries LIMIT 1 OFFSET ?", (offset,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "No entries")
            return {"id": r[0], "lemma": r[1], "pos": r[2], "date": today}
    return {}

@app.get("/entry/{entry_id}/synsets")
def entry_synsets(entry_id: str):
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT s.id, s.pos, s.def_en, s.def_ar FROM synsets s JOIN entry_synsets es ON es.synset_id=s.id WHERE es.entry_id=?", (entry_id,))
            rows = cur.fetchall()
        return [{"synset_id": r[0], "pos": r[1], "def_en": r[2], "def_ar": r[3]} for r in rows]
    return []

@app.get("/synset/{synset_id}")
def get_synset(synset_id: str):
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            cur.execute("SELECT id, pos, def_en, def_ar FROM synsets WHERE id=?", (synset_id,))
            s = cur.fetchone()
            if not s:
                raise HTTPException(404, "Synset not found")
            cur.execute("SELECT e.id, e.lemma_surface, e.pos FROM entry_synsets es JOIN entries e ON e.id=es.entry_id WHERE es.synset_id=?", (synset_id,))
            entries = [{"id": r[0], "lemma": r[1], "pos": r[2]} for r in cur.fetchall()]
        return {"id": s[0], "pos": s[1], "def_en": s[2], "def_ar": s[3], "entries": entries}
    return {}

# Dialect endpoints
@app.get("/dialects")
def list_dialects():
    """Get list of available dialects."""
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            try:
                cur.execute("SELECT id, name, countries, iso_code, speakers FROM dialects ORDER BY name")
                dialects = []
                for row in cur.fetchall():
                    countries = json.loads(row[2]) if row[2] else []
                    dialects.append({
                        "id": row[0],
                        "name": row[1], 
                        "countries": countries,
                        "iso_code": row[3],
                        "speakers": row[4]
                    })
                return dialects
            except sqlite3.OperationalError:
                return []
    return []

@app.get("/dialects/search")
def search_dialects(
    q: str = Query(..., min_length=1),
    dialect: Optional[str] = None,
    search_type: Optional[str] = "all",  # "dialect", "fusha", "english", "all"
    limit: int = 30
):
    """Search dialect words with fuzzy matching and autocomplete."""
    if not is_sqlite():
        return []
        
    with conn_sqlite() as c:
        cur = c.cursor()
        try:
            # Check if dialect tables exist
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dialect_words'")
            if not cur.fetchone():
                return []
                
            nq = norm(q)
            results = []
            
            # Direct matches first
            if search_type in ["dialect", "all"]:
                query = """
                    SELECT w.word, w.fusha, w.english, w.pronunciation, w.usage, w.examples, d.name
                    FROM dialect_words w JOIN dialects d ON d.id = w.dialect_id
                    WHERE w.word_norm = ?
                """
                params = [nq]
                if dialect:
                    query += " AND w.dialect_id = ?"
                    params.append(dialect)
                query += " LIMIT ?"
                params.append(limit)
                
                cur.execute(query, params)
                for row in cur.fetchall():
                    examples = json.loads(row[5]) if row[5] else []
                    results.append({
                        "word": row[0],
                        "fusha": row[1],
                        "english": row[2],
                        "pronunciation": row[3],
                        "usage": row[4],
                        "examples": examples,
                        "dialect": row[6],
                        "match_type": "exact"
                    })
            
            # Fusha to dialect lookup
            if search_type in ["fusha", "all"] and len(results) < limit:
                query = """
                    SELECT w.word, w.fusha, w.english, w.pronunciation, w.usage, w.examples, d.name
                    FROM dialect_words w JOIN dialects d ON d.id = w.dialect_id
                    WHERE w.fusha_norm = ?
                """
                params = [nq]
                if dialect:
                    query += " AND w.dialect_id = ?"
                    params.append(dialect)
                query += " LIMIT ?"
                params.append(limit - len(results))
                
                cur.execute(query, params)
                for row in cur.fetchall():
                    examples = json.loads(row[5]) if row[5] else []
                    results.append({
                        "word": row[0],
                        "fusha": row[1],
                        "english": row[2],
                        "pronunciation": row[3],
                        "usage": row[4],
                        "examples": examples,
                        "dialect": row[6],
                        "match_type": "fusha"
                    })
            
            # English to dialect lookup
            if search_type in ["english", "all"] and len(results) < limit:
                like_q = f"%{q}%"
                query = """
                    SELECT w.word, w.fusha, w.english, w.pronunciation, w.usage, w.examples, d.name
                    FROM dialect_words w JOIN dialects d ON d.id = w.dialect_id
                    WHERE w.english LIKE ? COLLATE NOCASE
                """
                params = [like_q]
                if dialect:
                    query += " AND w.dialect_id = ?"
                    params.append(dialect)
                query += " LIMIT ?"
                params.append(limit - len(results))
                
                cur.execute(query, params)
                for row in cur.fetchall():
                    examples = json.loads(row[5]) if row[5] else []
                    results.append({
                        "word": row[0],
                        "fusha": row[1],
                        "english": row[2],
                        "pronunciation": row[3],
                        "usage": row[4],
                        "examples": examples,
                        "dialect": row[6],
                        "match_type": "english"
                    })
            
            # FTS fuzzy search if we still need more results
            if len(results) < limit:
                try:
                    search_term = nq + "*"
                    query = """
                        SELECT w.word, w.fusha, w.english, w.pronunciation, w.usage, w.examples, d.name
                        FROM dialect_words w 
                        JOIN dialects d ON d.id = w.dialect_id
                        JOIN dialect_words_fts f ON f.rowid = w.rowid
                        WHERE dialect_words_fts MATCH ?
                    """
                    params = [search_term]
                    if dialect:
                        query += " AND w.dialect_id = ?"
                        params.append(dialect)
                    query += " LIMIT ?"
                    params.append(limit - len(results))
                    
                    cur.execute(query, params)
                    for row in cur.fetchall():
                        examples = json.loads(row[5]) if row[5] else []
                        # Avoid duplicates
                        if not any(r["word"] == row[0] and r["dialect"] == row[6] for r in results):
                            results.append({
                                "word": row[0],
                                "fusha": row[1],
                                "english": row[2],
                                "pronunciation": row[3],
                                "usage": row[4],
                                "examples": examples,
                                "dialect": row[6],
                                "match_type": "fuzzy"
                            })
                except sqlite3.OperationalError:
                    # FTS not available, skip fuzzy search
                    pass
            
            return results[:limit]
            
        except sqlite3.OperationalError as e:
            print(f"Dialect search error: {e}")
            return []

@app.get("/dialects/suggest")
def suggest_dialects(q: str = Query(..., min_length=1), dialect: Optional[str] = None, limit: int = 10):
    """Get autocomplete suggestions for dialect words."""
    if not is_sqlite():
        return []
        
    with conn_sqlite() as c:
        cur = c.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dialect_words'")
            if not cur.fetchone():
                return []
                
            nq = norm(q)
            
            # Try FTS prefix search first
            try:
                query = """
                    SELECT DISTINCT w.word
                    FROM dialect_words w
                    JOIN dialect_words_fts f ON f.rowid = w.rowid
                    WHERE dialect_words_fts MATCH ?
                """
                params = [nq + "*"]
                if dialect:
                    query += " AND w.dialect_id = ?"
                    params.append(dialect)
                query += " LIMIT ?"
                params.append(limit)
                
                cur.execute(query, params)
                return [row[0] for row in cur.fetchall()]
                
            except sqlite3.OperationalError:
                # Fallback to LIKE search
                like_q = f"{nq}%"
                query = """
                    SELECT DISTINCT w.word
                    FROM dialect_words w
                    WHERE w.word_norm LIKE ?
                """
                params = [like_q]
                if dialect:
                    query += " AND w.dialect_id = ?"
                    params.append(dialect)
                query += " LIMIT ?"
                params.append(limit)
                
                cur.execute(query, params)
                return [row[0] for row in cur.fetchall()]
                
        except sqlite3.OperationalError:
            return []

@app.get("/dialects/{dialect_id}")
def get_dialect_info(dialect_id: str):
    """Get detailed information about a specific dialect."""
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            try:
                # Get dialect info
                cur.execute("SELECT id, name, countries, iso_code, speakers FROM dialects WHERE id = ?", (dialect_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, "Dialect not found")
                
                countries = json.loads(row[2]) if row[2] else []
                
                # Get word count
                cur.execute("SELECT COUNT(*) FROM dialect_words WHERE dialect_id = ?", (dialect_id,))
                word_count = cur.fetchone()[0]
                
                return {
                    "id": row[0],
                    "name": row[1],
                    "countries": countries,
                    "iso_code": row[3],
                    "speakers": row[4],
                    "word_count": word_count
                }
            except sqlite3.OperationalError:
                raise HTTPException(404, "Dialect tables not found")
    return {}

# Advanced features for competitive edge
@app.get("/explore/root/{root}")
def explore_root_tree(root: str, limit: int = 50):
    """Get all derivatives of a root for tree visualization."""
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            # Clean root format
            clean_root = norm(root).replace('-', '')
            
            # Get all entries with this root
            cur.execute("""
                SELECT id, lemma_surface, pos, 
                       CASE WHEN root IS NOT NULL AND TRIM(root) != '' THEN 'exact'
                            ELSE 'pattern' END as match_type
                FROM entries 
                WHERE replace(coalesce(root,''), '-', '') = ? 
                   OR (root IS NULL AND lemma_norm LIKE ?)
                ORDER BY match_type, LENGTH(lemma_surface), lemma_surface
                LIMIT ?
            """, (clean_root, f'%{clean_root}%', limit))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "id": row[0],
                    "lemma": row[1],
                    "pos": row[2],
                    "match_type": row[3]
                })
            
            return {
                "root": root,
                "clean_root": clean_root,
                "derivatives": results,
                "count": len(results)
            }
    return {"root": root, "derivatives": [], "count": 0}

@app.get("/explore/semantic/{entry_id}")
def explore_semantic_network(entry_id: str, depth: int = 1):
    """Get semantic network around an entry (synonyms, antonyms, related words)."""
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            
            # Get the main entry
            cur.execute("SELECT id, lemma_surface, pos FROM entries WHERE id = ?", (entry_id,))
            main_entry = cur.fetchone()
            if not main_entry:
                raise HTTPException(404, "Entry not found")
            
            network = {
                "center": {"id": main_entry[0], "lemma": main_entry[1], "pos": main_entry[2]},
                "connections": {}
            }
            
            # Get relations from this entry
            try:
                cur.execute("""
                    SELECT r.type, r.target, r.target_entry_id, r.target_lang
                    FROM relations r
                    JOIN senses s ON s.sense_id = r.sense_id
                    WHERE s.entry_id = ?
                """, (entry_id,))
                
                for rel_type, target, target_id, target_lang in cur.fetchall():
                    if rel_type not in network["connections"]:
                        network["connections"][rel_type] = []
                    
                    connection = {
                        "target": target,
                        "target_lang": target_lang,
                        "target_id": target_id
                    }
                    
                    # If we have target_id, get more info
                    if target_id:
                        cur.execute("SELECT lemma_surface, pos FROM entries WHERE id = ?", (target_id,))
                        target_info = cur.fetchone()
                        if target_info:
                            connection.update({
                                "target_lemma": target_info[0],
                                "target_pos": target_info[1]
                            })
                    
                    network["connections"][rel_type].append(connection)
                    
            except sqlite3.OperationalError:
                pass  # Relations table not available
            
            # Get synset connections
            try:
                cur.execute("""
                    SELECT s.id, s.def_en, s.def_ar, s.pos
                    FROM synsets s
                    JOIN entry_synsets es ON es.synset_id = s.id
                    WHERE es.entry_id = ?
                """, (entry_id,))
                
                synsets = []
                for synset_id, def_en, def_ar, pos in cur.fetchall():
                    synsets.append({
                        "id": synset_id,
                        "def_en": def_en,
                        "def_ar": def_ar,
                        "pos": pos
                    })
                
                if synsets:
                    network["synsets"] = synsets
                    
            except sqlite3.OperationalError:
                pass
            
            return network
    return {}

@app.get("/analytics/popular")
def get_popular_words(pos: Optional[str] = None, limit: int = 20):
    """Get popular/frequently referenced words (for discovery)."""
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            
            # Simple heuristic: words with most translations + inflections
            query = """
                SELECT e.id, e.lemma_surface, e.pos, 
                       COUNT(DISTINCT t.id) as translation_count,
                       COUNT(DISTINCT i.id) as inflection_count,
                       (COUNT(DISTINCT t.id) + COUNT(DISTINCT i.id)) as popularity_score
                FROM entries e
                LEFT JOIN senses s ON s.entry_id = e.id
                LEFT JOIN translations t ON t.sense_id = s.sense_id
                LEFT JOIN inflections i ON i.entry_id = e.id
            """
            
            params = []
            if pos:
                query += " WHERE e.pos = ?"
                params.append(pos)
            
            query += """
                GROUP BY e.id, e.lemma_surface, e.pos
                HAVING popularity_score > 0
                ORDER BY popularity_score DESC, LENGTH(e.lemma_surface) ASC
                LIMIT ?
            """
            params.append(limit)
            
            cur.execute(query, params)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "id": row[0],
                    "lemma": row[1],
                    "pos": row[2],
                    "translation_count": row[3],
                    "inflection_count": row[4],
                    "popularity_score": row[5]
                })
            
            return results
    return []

@app.get("/learning/discovery")
def learning_discovery(level: str = "beginner", topic: Optional[str] = None, limit: int = 10):
    """Get curated word discovery for language learning."""
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            
            # Basic frequency-based curation
            if level == "beginner":
                # Short words, common POS, many translations
                query = """
                    SELECT e.id, e.lemma_surface, e.pos, 
                           COUNT(DISTINCT t.id) as richness
                    FROM entries e
                    JOIN senses s ON s.entry_id = e.id
                    JOIN translations t ON t.sense_id = s.sense_id
                    WHERE LENGTH(e.lemma_surface) <= 5
                      AND e.pos IN ('noun', 'verb', 'adj')
                """
            elif level == "intermediate":
                # Medium complexity, more varied POS
                query = """
                    SELECT e.id, e.lemma_surface, e.pos,
                           COUNT(DISTINCT t.id) as richness
                    FROM entries e
                    JOIN senses s ON s.entry_id = e.id
                    JOIN translations t ON t.sense_id = s.sense_id
                    WHERE LENGTH(e.lemma_surface) BETWEEN 4 AND 8
                """
            else:  # advanced
                # Complex words, rich etymology, many relations
                query = """
                    SELECT e.id, e.lemma_surface, e.pos,
                           COUNT(DISTINCT t.id) as richness
                    FROM entries e
                    JOIN senses s ON s.entry_id = e.id
                    JOIN translations t ON t.sense_id = s.sense_id
                    WHERE LENGTH(e.lemma_surface) >= 6
                      AND e.etymology IS NOT NULL
                """
            
            params = []
            if topic:
                # Simple topic matching in translations
                query += " AND t.text LIKE ?"
                params.append(f'%{topic}%')
            
            query += """
                GROUP BY e.id, e.lemma_surface, e.pos
                HAVING richness >= 2
                ORDER BY RANDOM()
                LIMIT ?
            """
            params.append(limit)
            
            cur.execute(query, params)
            
            results = []
            for row in cur.fetchall():
                # Get sample translation
                cur.execute("""
                    SELECT t.text 
                    FROM translations t 
                    JOIN senses s ON s.sense_id = t.sense_id 
                    WHERE s.entry_id = ? AND t.lang = 'en'
                    LIMIT 1
                """, (row[0],))
                
                translation = cur.fetchone()
                
                results.append({
                    "id": row[0],
                    "lemma": row[1],
                    "pos": row[2],
                    "sample_translation": translation[0] if translation else "",
                    "richness_score": row[3]
                })
            
            return {
                "level": level,
                "topic": topic,
                "words": results
            }
    return {"words": []}

@app.get("/stats")
def get_dictionary_stats():
    """Get comprehensive dictionary statistics."""
    if is_sqlite():
        with conn_sqlite() as c:
            cur = c.cursor()
            
            stats = {}
            
            # Core statistics
            cur.execute("SELECT COUNT(*) FROM entries")
            stats["total_entries"] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM senses")
            stats["total_senses"] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM translations WHERE lang = 'en'")
            stats["english_translations"] = cur.fetchone()[0]
            
            # POS distribution
            cur.execute("""
                SELECT pos, COUNT(*) 
                FROM entries 
                WHERE pos IS NOT NULL 
                GROUP BY pos 
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            stats["pos_distribution"] = [{"pos": row[0], "count": row[1]} for row in cur.fetchall()]
            
            # Dialect statistics
            try:
                cur.execute("SELECT COUNT(*) FROM dialects")
                stats["dialect_count"] = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM dialect_words")
                stats["dialect_words"] = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT d.name, COUNT(dw.id) as word_count
                    FROM dialects d
                    LEFT JOIN dialect_words dw ON dw.dialect_id = d.id
                    GROUP BY d.id, d.name
                    ORDER BY word_count DESC
                """)
                stats["dialect_distribution"] = [
                    {"dialect": row[0], "words": row[1]} 
                    for row in cur.fetchall()
                ]
            except sqlite3.OperationalError:
                stats["dialect_count"] = 0
                stats["dialect_words"] = 0
            
            # Semantic network stats
            try:
                cur.execute("SELECT COUNT(*) FROM synsets")
                stats["synsets"] = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM entry_synsets")
                stats["semantic_links"] = cur.fetchone()[0]
            except sqlite3.OperationalError:
                stats["synsets"] = 0
                stats["semantic_links"] = 0
            
            # Relations stats
            try:
                cur.execute("SELECT COUNT(*) FROM relations")
                stats["total_relations"] = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT type, COUNT(*) 
                    FROM relations 
                    GROUP BY type 
                    ORDER BY COUNT(*) DESC
                """)
                stats["relation_types"] = [
                    {"type": row[0], "count": row[1]} 
                    for row in cur.fetchall()
                ]
            except sqlite3.OperationalError:
                stats["total_relations"] = 0
                stats["relation_types"] = []
            
            return stats
    return {}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
