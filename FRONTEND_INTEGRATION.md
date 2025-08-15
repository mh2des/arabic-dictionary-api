# Arabic Dictionary API - Frontend Integration Guide

## 🚀 **Your Railway API URL**
After deploying on Railway, your API URL will be:
```
https://web-production-XXXX.up.railway.app
```
Replace `XXXX` with your actual Railway deployment ID.

## 📚 **Core API Endpoints for Frontend**

### **1. Main Search & Suggestions (Flutter Optimized)**

#### **🔍 Fast Search** - Primary search endpoint
```bash
GET /api/search/fast?q={search_term}&limit=20
```
**Example:**
```javascript
const response = await fetch(`${API_URL}/api/search/fast?q=كتاب&limit=10`);
const data = await response.json();
// Returns: {results: [{lemma, pos, root, definition}], count: number}
```

#### **💡 Auto-suggest** - For search-as-you-type
```bash
GET /api/suggest?q={partial_word}&limit=10
```
**Example:**
```javascript
const response = await fetch(`${API_URL}/api/suggest?q=كت&limit=5`);
const data = await response.json();
// Returns: {suggestions: [string], count: number}
```

### **2. Detailed Word Information**

#### **📖 Enhanced Search** - Full linguistic details
```bash
GET /search/enhanced?q={word}&include_camel=true&include_phonetics=true
```

#### **🔍 Get Specific Word**
```bash
GET /lemmas/{word}
```

#### **🌳 Search by Root**
```bash
GET /root/{root}
```

### **3. Mobile App Screens (Enhanced APIs)**

#### **Screen 1: Word Info**
```bash
GET /word/{lemma}/info
```

#### **Screen 2: Word Senses**
```bash
GET /word/{lemma}/senses
```

#### **Screen 4: Word Relations**
```bash
GET /word/{lemma}/relations
```

#### **Screen 5: Pronunciation**
```bash
GET /word/{lemma}/pronunciation
```

### **4. Health & Status**

#### **Basic Health Check**
```bash
GET /health
```

#### **Detailed Status**
```bash
GET /
# Returns database stats, available features, endpoints
```

#### **Database Verification**
```bash
GET /comprehensive/verify
# Check if comprehensive database is loaded
```

## 🔧 **Frontend Integration Examples**

### **React/JavaScript Example:**

```javascript
class ArabicDictionary {
  constructor(apiUrl) {
    this.apiUrl = apiUrl; // Your Railway URL
  }

  // Search for words
  async search(query, limit = 20) {
    try {
      const response = await fetch(
        `${this.apiUrl}/api/search/fast?q=${encodeURIComponent(query)}&limit=${limit}`
      );
      return await response.json();
    } catch (error) {
      console.error('Search failed:', error);
      return { results: [], count: 0 };
    }
  }

  // Get suggestions for autocomplete
  async getSuggestions(query, limit = 10) {
    try {
      const response = await fetch(
        `${this.apiUrl}/api/suggest?q=${encodeURIComponent(query)}&limit=${limit}`
      );
      return await response.json();
    } catch (error) {
      console.error('Suggestions failed:', error);
      return { suggestions: [], count: 0 };
    }
  }

  // Get detailed word information
  async getWordDetails(lemma) {
    try {
      const response = await fetch(
        `${this.apiUrl}/lemmas/${encodeURIComponent(lemma)}`
      );
      return await response.json();
    } catch (error) {
      console.error('Word details failed:', error);
      return null;
    }
  }

  // Check API health
  async checkHealth() {
    try {
      const response = await fetch(`${this.apiUrl}/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'error' };
    }
  }
}

// Usage
const api = new ArabicDictionary('https://your-railway-url.up.railway.app');

// Search example
const searchResults = await api.search('كتاب');
console.log(searchResults.results);

// Suggestions example
const suggestions = await api.getSuggestions('كت');
console.log(suggestions.suggestions);
```

### **Flutter/Dart Example:**

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ArabicDictionaryAPI {
  final String baseUrl;
  
  ArabicDictionaryAPI(this.baseUrl);

  // Search for words
  Future<Map<String, dynamic>> search(String query, {int limit = 20}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/search/fast?q=${Uri.encodeComponent(query)}&limit=$limit'),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'results': [], 'count': 0};
    } catch (e) {
      print('Search error: $e');
      return {'results': [], 'count': 0};
    }
  }

  // Get suggestions
  Future<Map<String, dynamic>> getSuggestions(String query, {int limit = 10}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/suggest?q=${Uri.encodeComponent(query)}&limit=$limit'),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'suggestions': [], 'count': 0};
    } catch (e) {
      print('Suggestions error: $e');
      return {'suggestions': [], 'count': 0};
    }
  }

  // Get word details
  Future<Map<String, dynamic>?> getWordDetails(String lemma) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/lemmas/${Uri.encodeComponent(lemma)}'),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Word details error: $e');
      return null;
    }
  }
}

// Usage
final api = ArabicDictionaryAPI('https://your-railway-url.up.railway.app');

// Search example
final results = await api.search('كتاب');
print('Found ${results['count']} results');

// Suggestions example  
final suggestions = await api.getSuggestions('كت');
print('Suggestions: ${suggestions['suggestions']}');
```

## 🎯 **Key Features for Your Frontend:**

1. **✅ Fast Search**: Optimized for real-time search
2. **✅ Auto-suggestions**: Perfect for search-as-you-type
3. **✅ Arabic Text Support**: Proper URL encoding handled
4. **✅ Comprehensive Data**: 101,331+ Arabic words
5. **✅ Multiple Screens**: Ready-made APIs for different app screens
6. **✅ Error Handling**: Robust error responses
7. **✅ CORS Enabled**: Works with web frontends
8. **✅ High Performance**: Indexed database searches

## 🔗 **After Railway Deployment:**

1. **Get your URL** from Railway dashboard
2. **Test the endpoints** using the examples above
3. **Integrate into your frontend** using the provided code
4. **Handle Arabic text** with proper URL encoding
5. **Implement error handling** for network issues

Your comprehensive Arabic dictionary API will be ready for production use! 🚀
