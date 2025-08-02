import re

# Read the auth.py file
with open("app/api/v1/endpoints/auth.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove all rate limiting decorators
content = re.sub(r'@limiter\.limit\([^)]+\)\s*\n', '', content)

# Remove limiter import
content = re.sub(r'.*from app\.core\.limiter import limiter.*\n', '', content)

# Write back
with open("app/api/v1/endpoints/auth.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Rate limiting disabled. Restart your server now.")