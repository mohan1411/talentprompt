#!/bin/bash

echo "CORS Configuration Checker for Promtitude"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend URL
BACKEND_URL="https://talentprompt-production.up.railway.app"

echo -e "\n${YELLOW}1. Checking if backend is accessible...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/health" | grep -q "200\|503"; then
    echo -e "${GREEN}✓ Backend is accessible${NC}"
else
    echo -e "${RED}✗ Backend is not accessible or down${NC}"
    echo "Please check Railway dashboard for service status"
    exit 1
fi

echo -e "\n${YELLOW}2. Checking CORS headers...${NC}"
CORS_HEADER=$(curl -s -I -X OPTIONS "$BACKEND_URL/api/v1/auth/login" \
    -H "Origin: https://promtitude.com" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    | grep -i "access-control-allow-origin")

if [ -z "$CORS_HEADER" ]; then
    echo -e "${RED}✗ No CORS headers found${NC}"
    echo ""
    echo "To fix this issue:"
    echo "1. Go to Railway dashboard (https://railway.app)"
    echo "2. Navigate to your backend service"
    echo "3. Go to Variables tab"
    echo "4. Add or update BACKEND_CORS_ORIGINS with:"
    echo '   ["https://promtitude.com","https://www.promtitude.com","https://api.promtitude.com"]'
    echo "5. Restart the service"
else
    echo -e "${GREEN}✓ CORS headers found: $CORS_HEADER${NC}"
    
    if echo "$CORS_HEADER" | grep -q "promtitude.com"; then
        echo -e "${GREEN}✓ promtitude.com is allowed${NC}"
    else
        echo -e "${RED}✗ promtitude.com is NOT in allowed origins${NC}"
        echo "Update BACKEND_CORS_ORIGINS in Railway to include promtitude.com"
    fi
fi

echo -e "\n${YELLOW}3. Testing preflight request...${NC}"
PREFLIGHT_RESPONSE=$(curl -s -X OPTIONS "$BACKEND_URL/api/v1/auth/login" \
    -H "Origin: https://promtitude.com" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$PREFLIGHT_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "204" ]; then
    echo -e "${GREEN}✓ Preflight request successful (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ Preflight request failed (HTTP $HTTP_CODE)${NC}"
fi

echo -e "\n${YELLOW}4. Current Railway Environment Variables Needed:${NC}"
cat << EOF
BACKEND_CORS_ORIGINS=["https://promtitude.com","https://www.promtitude.com","https://api.promtitude.com"]
EOF

echo -e "\n${YELLOW}5. Quick Test Command:${NC}"
echo 'curl -X POST https://talentprompt-production.up.railway.app/api/v1/auth/login \'
echo '  -H "Origin: https://promtitude.com" \'
echo '  -H "Content-Type: application/x-www-form-urlencoded" \'
echo '  -d "username=test@example.com&password=test" \'
echo '  -v 2>&1 | grep -i "access-control"'