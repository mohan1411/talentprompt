#!/bin/bash
# Test the analyze-query endpoint directly with curl

TOKEN=$1
if [ -z "$TOKEN" ]; then
    echo "Usage: ./test_endpoint_curl.sh YOUR_ACCESS_TOKEN"
    exit 1
fi

echo "Testing analyze-query endpoint with curl..."
echo "=========================================="

curl -X POST "http://localhost:8001/api/v1/search/analyze-query?query=Pythonn%20Developer" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{}' \
     -s | python -m json.tool