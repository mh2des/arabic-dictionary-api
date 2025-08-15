#!/bin/bash
# API Testing Script for Arabic Dictionary
# Replace YOUR_RAILWAY_URL with your actual Railway deployment URL

API_URL="https://your-railway-url.up.railway.app"

echo "🧪 Testing Arabic Dictionary API"
echo "================================"

echo "1. Health Check:"
curl -s "$API_URL/health" | head -c 200
echo -e "\n"

echo "2. API Info:"
curl -s "$API_URL/" | head -c 300
echo -e "\n"

echo "3. Fast Search (كتاب):"
curl -s "$API_URL/api/search/fast?q=كتاب&limit=5" | head -c 500
echo -e "\n"

echo "4. Suggestions (كت):"
curl -s "$API_URL/api/suggest?q=كت&limit=3" | head -c 300
echo -e "\n"

echo "5. Database Verification:"
curl -s "$API_URL/comprehensive/verify" | head -c 400
echo -e "\n"

echo "🎯 Replace YOUR_RAILWAY_URL with your actual Railway URL!"
echo "   Example: https://web-production-f0d6.up.railway.app"
