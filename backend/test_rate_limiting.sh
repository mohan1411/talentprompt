#!/bin/bash
# Test rate limiting on various endpoints

echo "Testing rate limiting on login endpoint (5/minute limit)..."
for i in {1..7}; do
    echo "Attempt $i:"
    curl -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"test@example.com","password":"wrongpass"}' \
        -w "\nStatus: %{http_code}\n"
    sleep 1
done

echo "\nTesting rate limiting on register endpoint (3/hour limit)..."
for i in {1..5}; do
    echo "Attempt $i:"
    curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"email":"test'$i'@example.com","username":"test'$i'","password":"TestPass123!"}' \
        -w "\nStatus: %{http_code}\n"
    sleep 1
done

echo "\nRate limiting test complete!"
echo "You should see 429 (Too Many Requests) status codes after the limits are exceeded."
