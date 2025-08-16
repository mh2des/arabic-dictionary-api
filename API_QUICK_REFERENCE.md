# 🎯 Quick API Reference - Arabic Dictionary

## 🔥 Core Endpoints for Flutter Screens

### Screen 1: Search & Autocomplete
```
GET /api/suggest?q={query}           // Real-time suggestions
GET /api/search/fast?q={query}       // Fast search results
```

### Screen 2: Word Details 
```
GET /word/{lemma}/complete           // Full word data
GET /word/{lemma}/senses            // Word meanings
GET /word/{lemma}/pronunciation     // Phonetic data
GET /word/{lemma}/relations         // Related words
```

### Screen 3: Root Analysis
```
GET /root/{root}                    // Words by root
GET /dialect/search/root/{root}     // Enhanced root search
```

### Screen 4: Dialect Support
```
GET /dialect/analyze/{word}         // Live dialect analysis
GET /dialect/variants/{word}        // Dialect variants
```

### Screen 5: Advanced Features
```
GET /search/enhanced?q={query}      // Advanced search
GET /stats/comprehensive            // Database stats
GET /random                         // Random word
```

---

## 📊 Key Response Models

### Basic Word Entry:
```json
{
  "lemma": "كِتَاب",          // Arabic word
  "root": "ك ت ب",           // Root letters  
  "pos": "noun",             // Part of speech
  "freq_rank": 245           // Frequency ranking
}
```

### Enhanced Entry (Complete):
```json
{
  "basic_info": {
    "id": 12345,
    "lemma": "كِتَاب",
    "root": "ك ت ب",
    "pos": "noun",
    "freq_rank": 245
  },
  "camel_analysis": {
    "lemmas": ["كِتَاب", "كُتُب"],
    "roots": ["ك ت ب"],
    "confidence": 0.95
  },
  "phonetic_data": {
    "buckwalter": "kitAb",
    "ipa_transcription": {"ipa": "kitaːb"}
  }
}
```

---

## 🚀 Database Stats
- **101,331 comprehensive entries**
- **Real Arabic vocabulary** (not samples)
- **CAMeL Tools integration** for morphological analysis
- **Phonetic transcription** available
- **Root-based relationships**
- **Dialect support**

---

## 🎨 Flutter Usage Examples

```dart
// Search suggestions as user types
final suggestions = await api.get('/api/suggest?q=كت');

// Get complete word details
final wordData = await api.get('/word/كِتَاب/complete');

// Find words by root
final rootWords = await api.get('/root/ك ت ب');

// Get pronunciation
final pronunciation = await api.get('/word/كِتَاب/pronunciation');
```

---

## 📱 Recommended Screen Structure

1. **Search Screen**: `/api/suggest` + `/api/search/fast`
2. **Word Details**: `/word/{lemma}/complete`
3. **Pronunciation**: `/word/{lemma}/pronunciation` 
4. **Related Words**: `/word/{lemma}/relations`
5. **Root Analysis**: `/root/{root}`
6. **Dialect Info**: `/dialect/analyze/{word}`

**Base URL**: `https://your-render-app.onrender.com`

**All endpoints support CORS and are optimized for mobile performance!** 📱✨
