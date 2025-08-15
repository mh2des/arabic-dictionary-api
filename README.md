# Arabic Dictionary Backend (Full Skeleton)

This repository provides a **production‑grade skeleton** for an Arabic dictionary
backend.  It is designed to ingest multiple open resources, normalise and
merge their content and serve it via a FastAPI service for consumption by
mobile or web clients.  The project emphasises **rich linguistic
annotations**, **fast search**, **extensibility** and **legal compliance** with
open data licences.

## Key Features

* **Extensible data model** including high‑level info, multiple senses,
  examples, semantic relations, pronunciation, dialect variants,
  inflection tables and derived forms.  See the JSON Schema in
  `schema.json` for a formal definition.
* **Modular ETL pipeline** under `app/etl` to ingest data from:
  - Arramooz AlWaseet for morphology.
  - Arabic WordNet & Sinalab Synonyms for semantic relations.
  - ArabicLT (Radif) for synonyms and antonyms.
  - Wiktionary via the MediaWiki API for definitions, translations and examples.
  - Qutrub for conjugation.
* **Arabic normalisation** implemented in `app/services/normalize.py` for
  robust searching across orthographic variations.  Normalisation
  includes diacritic stripping and unification of variant letters
  (أ/إ/آ→ا, ى→ي, ؤ→و, ئ→ي, lam‑alif ligatures, etc.).
* **Fast search API** powered by SQLite FTS5 (default) or PostgreSQL
  depending on configuration.  The `search.py` service layer
  encapsulates indexing and ranking logic.
* **Pluggable TTS** endpoint stub in `app/services/tts.py` for
  integration with providers such as Google Cloud or Azure.  Disabled by
  default.
* **Comprehensive scripts** in the `scripts` directory to ingest
  sources, build the database, export JSONL bundles and run tests.
* **Tests and benchmarks** in `tests` verify normalisation, merging and
  API behaviour.  Additional data QA notebooks can be added under
  `tests/qa`.
* **Docker and Docker Compose** files for reproducible deployment.
* **Configuration** via TOML file (`config/settings.example.toml`) and
  environment variables to toggle features and adjust database
  settings.

## Getting Started

1. Create and activate a Python virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `config/settings.example.toml` to `config/settings.toml` and
   customise as needed.  At minimum set the `database_url` to point to
   your SQLite or PostgreSQL instance.

4. Run the ETL pipeline to ingest all sources.  This will download
   resources (when permissible), normalise entries and write a
   consolidated JSONL file:

   ```bash
   bash scripts/ingest_all.sh
   ```

5. Build the search indices and initialise the database:

   ```bash
   bash scripts/build_all.sh
   ```

6. Start the API server:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Access the interactive API docs at http://localhost:8000/docs and
   explore the endpoints.  For example, to look up the lemma
   **أكل**:

   ```bash
   curl 'http://localhost:8000/lemmas/أكل'
   ```

## Project Structure

```
backend/
├── app/                # Application code
│   ├── __init__.py
│   ├── main.py         # FastAPI entrypoint and routing
│   ├── api/            # Route modules (can be expanded)
│   ├── models/         # Pydantic models and JSON Schema
│   ├── services/       # Business logic: normalisation, search, TTS
│   ├── data/
│   │   └── sample/
│   │       └── sample_entries.json  # Small sample dataset
│   ├── etl/            # Extract–Transform–Load pipeline
│   ├── db/             # Database schema and helpers
│   └── config/         # Example TOML configuration
├── tests/              # Unit tests and QA notebooks
├── scripts/            # Helper scripts for build, ingest, export
├── schema.json         # JSON Schema for lexical entries
├── Dockerfile          # Docker build instructions
├── docker-compose.yml  # Compose file for dev and prod
├── requirements.txt    # Python package dependencies
├── LICENSE             # Project licence (MIT)
├── CHANGELOG.md        # Release notes
└── CONTRIBUTING.md     # Contribution guidelines
```

## Licence

This project is distributed under the MIT Licence.  See `LICENSE` for
details.  Individual data sources may have their own licences; ensure
you respect them when ingesting and distributing data.
