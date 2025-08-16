# 🚀 Comprehensive Arabic Dictionary API - Frontend Integration Guide

## 📊 Database Schema Overview

**Database:** SQLite with **101,331 comprehensive Arabic entries**

### Core Entry Structure:
```json
{
  "id": 12345,
  "lemma": "كِتَاب",           // Original Arabic word
  "lemma_norm": "كتاب",        // Normalized form  
  "root": "ك ت ب",            // Root letters
  "pos": "noun",              // Part of speech
  "subpos": "masculine",      // Sub-category
  "register": "standard",     // Language register
  "domain": "education",      // Semantic domain
  "freq_rank": 245,           // Frequency ranking
  
  // Enhanced CAMeL Tools Data:
  "camel_lemmas": ["كِتَاب", "كُتُب"],
  "camel_roots": ["ك ت ب"],
  "camel_pos_tags": ["noun", "noun_prop"],
  "camel_confidence": 0.95,
  
  // Phonetic Data:
  "buckwalter_transliteration": "kitAb",
  "phonetic_transcription": {"ipa": "kitaːb"},
  "semantic_features": {"category": "object", "animacy": "inanimate"}
}
```

---

## 🎯 Screen 1: Search & Suggestions

### **Fast Autocomplete** (Real-time typing)
```http
GET /api/suggest?q={query}
```

**Use for:** Search bar autocomplete as user types

**Response:**
```json
{
  "suggestions": [
    {
      "lemma": "كِتَاب",
      "root": "ك ت ب", 
      "pos": "noun"
    }
  ]
}
```

### **Quick Search** (Search button)
```http
GET /api/search/fast?q={query}
```

**Use for:** Fast search results for mobile performance

**Response:**
```json
{
  "results": [
    {
      "id": 12345,
      "lemma": "كِتَاب",
      "lemma_norm": "كتاب",
      "root": "ك ت ب",
      "pos": "noun",
      "subpos": "masculine",
      "register": "standard",
      "domain": "education",
      "freq_rank": 245
    }
  ]
}
```

---

## 🎯 Screen 2: Word Details Page

### **Complete Word Information**
```http
GET /word/{lemma}/complete
```

**Use for:** Full word details screen

**Response:**
```json
{
  "basic_info": {
    "id": 12345,
    "lemma": "كِتَاب",
    "lemma_norm": "كتاب", 
    "root": "ك ت ب",
    "pos": "noun",
    "subpos": "masculine",
    "register": "standard",
    "domain": "education",
    "freq_rank": 245
  },
  "camel_analysis": {
    "lemmas": ["كِتَاب", "كُتُب"],
    "roots": ["ك ت ب"],
    "pos_tags": ["noun", "noun_prop"],
    "confidence": 0.95
  },
  "phonetic_data": {
    "buckwalter": "kitAb",
    "ipa_transcription": {"ipa": "kitaːb"}
  },
  "semantic_data": {
    "category": "object",
    "animacy": "inanimate"
  },
  "enhancement_status": {
    "camel_analyzed": true,
    "phonetic_enhanced": true,
    "semantic_enhanced": true
  }
}
```

### **Word Meanings & Senses**
```http
GET /word/{lemma}/senses
```

**Use for:** Meanings and definitions section

**Response:**
```json
{
  "senses": [
    {
      "type": "semantic",
      "data": {"category": "object", "animacy": "inanimate"}
    },
    {
      "type": "camel_analysis", 
      "lemmas": ["كِتَاب", "كُتُب"]
    },
    {
      "type": "grammatical",
      "pos": "noun",
      "subpos": "masculine",
      "domain": "education"
    }
  ],
  "total_count": 3
}
```

---

## 🎯 Screen 3: Root Analysis

### **Words by Root**
```http
GET /root/{root}
```

**Use for:** Show all words sharing the same root

**Response:**
```json
[
  {
    "lemma": "كِتَاب",
    "root": "ك ت ب",
    "pos": "noun"
  },
  {
    "lemma": "كَاتِب", 
    "root": "ك ت ب",
    "pos": "noun"
  },
  {
    "lemma": "مَكْتَبَة",
    "root": "ك ت ب", 
    "pos": "noun"
  }
]
```

### **Enhanced Root Search** (with dialects)
```http
GET /dialect/search/root/{root}
```

**Use for:** Advanced root analysis with dialect variants

---

## 🎯 Screen 4: Pronunciation & Phonetics

### **Pronunciation Data**
```http
GET /word/{lemma}/pronunciation
```

**Use for:** Pronunciation guide and audio preparation

**Response:**
```json
{
  "pronunciations": [
    {
      "type": "buckwalter",
      "transcription": "kitAb"
    },
    {
      "type": "ipa", 
      "transcription": {"ipa": "kitaːb"}
    }
  ],
  "phonetic_variants": ["kitAb", "kitaːb"]
}
```

### **Simple Phonetics**
```http
GET /phonetics/{word}
```

**Use for:** Quick phonetic lookup

**Response:**
```json
{
  "word": "كِتَاب",
  "buckwalter": "kitAb",
  "phonetic": {"ipa": "kitaːb"},
  "status": "found"
}
```

---

## 🎯 Screen 5: Dialect Support

### **Dialect Analysis**
```http
GET /dialect/analyze/{word}
```

**Use for:** Real-time dialect analysis with CAMeL Tools

**Response:**
```json
{
  "word": "كِتَاب",
  "normalized": "كتاب",
  "analysis": {
    "lemmas": ["كِتَاب"],
    "roots": ["ك ت ب"],
    "pos_tags": ["noun"],
    "confidence": 0.95,
    "analyses": [
      {
        "lex": "كِتَاب",
        "root": "ك ت ب", 
        "pos": "noun"
      }
    ],
    "live_analysis": true
  },
  "dialect_info": {
    "register": "standard",
    "variants": []
  }
}
```

### **Dialect Variants**
```http
GET /dialect/variants/{word}
```

**Use for:** Show different dialect forms of a word

### **Dialect Coverage Stats**
```http
GET /dialect/coverage/stats
```

**Use for:** Show dialect analysis capabilities

---

## 🎯 Screen 6: Word Relationships

### **Related Words**
```http
GET /word/{lemma}/relations
```

**Use for:** Show semantically or morphologically related words

**Response:**
```json
{
  "relations": [
    {
      "type": "same_root",
      "root": "ك ت ب",
      "related_words": [
        {"lemma": "كَاتِب", "pos": "noun"},
        {"lemma": "مَكْتَبَة", "pos": "noun"}
      ]
    },
    {
      "type": "camel_root",
      "root": "ك ت ب",
      "related_words": [
        {"lemma": "كِتَابَة", "pos": "noun"}
      ]
    }
  ],
  "total_count": 15
}
```

---

## 🎯 Screen 7: Enhanced Search

### **Advanced Search**
```http
GET /search/enhanced?q={query}&limit=50
```

**Use for:** Advanced search with filtering options

**Response:**
```json
{
  "results": [
    {
      "id": 12345,
      "lemma": "كِتَاب",
      "lemma_norm": "كتاب",
      "root": "ك ت ب",
      "pos": "noun",
      "subpos": "masculine", 
      "register": "standard",
      "domain": "education",
      "freq_rank": 245,
      "camel_lemmas": ["كِتَاب", "كُتُب"],
      "camel_roots": ["ك ت ب"],
      "camel_pos_tags": ["noun"],
      "camel_confidence": 0.95,
      "buckwalter_transliteration": "kitAb",
      "phonetic_transcription": {"ipa": "kitaːb"},
      "semantic_features": {"category": "object"},
      "phase2_enhanced": true,
      "camel_analyzed": true
    }
  ],
  "total": 156
}
```

---

## 📈 Additional Utility Endpoints

### **Random Word** (Word of the Day)
```http
GET /random
```

### **Database Statistics**
```http
GET /stats/comprehensive
```

**Response:**
```json
{
  "database_info": {
    "total_entries": 101331,
    "unique_roots": 5247,
    "pos_categories": 15,
    "status": "comprehensive_database_loaded"
  },
  "enhancement_coverage": {
    "camel_analyzed": 95680,
    "phonetic_enhanced": 78234,
    "buckwalter_available": 89456,
    "coverage_percentage": {
      "camel": 94.4,
      "phonetic": 77.2,
      "buckwalter": 88.3
    }
  },
  "pos_distribution": [
    {"pos": "noun", "count": 45678},
    {"pos": "verb", "count": 23456}
  ]
}
```

### **Health Check**
```http
GET /health
```

### **Test All Functionality**
```http
GET /test/screens
```

---

## 🎨 Flutter Integration Tips

### **1. Search Screen Implementation:**
```dart
// Real-time suggestions as user types
Future<List<Suggestion>> getSuggestions(String query) async {
  final response = await http.get('$baseUrl/api/suggest?q=$query');
  return SuggestionResponse.fromJson(response.data).suggestions;
}

// Search results when user presses search
Future<List<WordEntry>> fastSearch(String query) async {
  final response = await http.get('$baseUrl/api/search/fast?q=$query');
  return SearchResponse.fromJson(response.data).results;
}
```

### **2. Word Details Screen:**
```dart
// Complete word information
Future<CompleteWordData> getWordDetails(String lemma) async {
  final response = await http.get('$baseUrl/word/$lemma/complete');
  return CompleteWordData.fromJson(response.data);
}

// Individual sections
Future<List<Sense>> getWordSenses(String lemma) async {
  final response = await http.get('$baseUrl/word/$lemma/senses');
  return SenseResponse.fromJson(response.data).senses;
}
```

### **3. Root Analysis Screen:**
```dart
Future<List<BasicInfo>> getWordsByRoot(String root) async {
  final response = await http.get('$baseUrl/root/$root');
  return (response.data as List).map((e) => BasicInfo.fromJson(e)).toList();
}
```

### **4. Pronunciation Screen:**
```dart
Future<PronunciationData> getPronunciation(String lemma) async {
  final response = await http.get('$baseUrl/word/$lemma/pronunciation');
  return PronunciationResponse.fromJson(response.data);
}
```

---

## 🔧 Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Word not found"  // HTTP 404
}
{
  "detail": "Database connection failed"  // HTTP 500
}
```

---

## 🌐 Base URL

**Production:** `https://arabic-dictionary-api.onrender.com`

**All endpoints support CORS and are ready for Flutter integration.**

---

## 📱 Screen Flow Recommendations

1. **Search Screen** → Use `/api/suggest` + `/api/search/fast`
2. **Word Detail Screen** → Use `/word/{lemma}/complete` 
3. **Pronunciation Tab** → Use `/word/{lemma}/pronunciation`
4. **Relations Tab** → Use `/word/{lemma}/relations`
5. **Root Analysis** → Use `/root/{root}`
6. **Dialect Analysis** → Use `/dialect/analyze/{word}`
7. **Enhanced Search** → Use `/search/enhanced`

**Your comprehensive Arabic dictionary API is now ready for full Flutter integration with 101,331 real entries!** 🚀
