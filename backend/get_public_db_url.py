#!/usr/bin/env python3
"""Get the public database URL."""

import os

# Try different possible environment variables
for var in ['DATABASE_PUBLIC_URL', 'DATABASE_URL', 'POSTGRES_URL']:
    url = os.environ.get(var)
    if url:
        print(f"{var}: {url}")

print("\nTo get the public URL:")
print("1. Go to your Railway dashboard")
print("2. Click on your PostgreSQL service")
print("3. Go to the 'Connect' tab")
print("4. Look for 'Postgres Connection URL' or 'Public Network'")
print("5. Copy that URL")