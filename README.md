# 🚀 Arabic Dictionary API

A comprehensive Arabic dictionary API with dialect support, semantic networks, and advanced search capabilities.

## 📊 Features

- **74,977 Arabic entries** with rich semantic data
- **10 Arabic dialects** with 6,420+ regional words
- **Smart search** with fuzzy matching and autocomplete
- **Root exploration** for Arabic morphology
- **Semantic networks** with WordNet integration
- **Learning discovery** system for language learners

## 🔗 API Endpoints

### Core Dictionary
- `GET /lookup?q={query}` - Main search endpoint
- `GET /suggest?q={prefix}` - Autocomplete suggestions  
- `GET /reverse?q={english}` - English to Arabic lookup
- `GET /entry/{id}` - Get detailed word information

### Dialects
- `GET /dialects` - List all supported dialects
- `GET /dialects/search?q={query}` - Search dialect words
- `GET /dialects/{id}` - Get dialect details

### Advanced Features
- `GET /explore/root/{root}` - Root-based word exploration
- `GET /explore/semantic/{id}` - Semantic relationship network
- `GET /etymology/{id}` - Etymology and word history
- `GET /learning/discovery` - Curated learning content
- `GET /analytics/popular` - Popular words
- `GET /stats` - Dictionary statistics

## 🚀 Deployment

### Render (Recommended)
1. Fork this repository
2. Connect to Render
3. Deploy using `render.yaml` configuration
4. API will be available at your Render URL

### Local Development
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentation

- Interactive API docs: `/docs` 
- OpenAPI spec: `/openapi.json`
- Production guide: `PRODUCTION_READY.md`
- Flutter app guide: `FLUTTER_DEVELOPMENT_GUIDE.md`

## 🎯 Use Cases

- Arabic language learning apps
- Translation services
- Linguistic research tools
- Educational platforms
- Dialect exploration apps

## 📈 Statistics

- 74,977 total entries
- 96,904 word senses
- 55,975 English translations
- 10 Arabic dialects supported
- 10,414 semantic synsets

## 🔧 Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLite** - Lightweight database with FTS5
- **Uvicorn** - ASGI server
- **orjson** - Fast JSON responses

## 📄 License

Open source - ready for integration into Arabic language applications.
- GET /synset/{synset_id}

**Dialect endpoints:**
- GET /dialects - List available dialects
- GET /dialects/search?q=word&dialect=sudanese&search_type=all
- GET /dialects/suggest?q=prefix&dialect=egyptian
- GET /dialects/{dialect_id} - Get dialect info

Notes
- Arabic normalization removes diacritics/tatweel and unifies alef/hamza and yaa/maqsurah.
- FTS5 powers fuzzy and autocomplete in SQLite.
- Set `ALLOW_ORIGINS` to control CORS.
- Switch to Postgres later by setting `DB_DSN` and adapting the schema.

## Docker
Build and run the API in Docker:
```bash
docker build -t arabic-dict .
docker run -it --rm -p 8080:8080 -e SQLITE_DB=/app/dict.db arabic-dict
```

## Deployment tips
- Use the provided Dockerfile or Procfile.
- Pre-generate `dict.db` in CI or at first boot using `load_sqlite.py`.
- Set `SQLITE_DB` and `ALLOW_ORIGINS` via environment.

