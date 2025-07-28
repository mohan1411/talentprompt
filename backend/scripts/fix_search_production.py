#!/usr/bin/env python3
"""Quick fix for production search issues."""

import os
import sys

print("="*60)
print("PRODUCTION SEARCH FIX")
print("="*60)

print("\nThis script will fix the search error in production.")
print("\nPlease run the following command in Railway CLI:")
print("\n" + "="*60)
print("railway run python backend/scripts/fix_fulltext_columns.py")
print("="*60)

print("\nThis will:")
print("1. Check your database columns")
print("2. Drop any indexes referencing non-existent columns")
print("3. Create correct indexes for search functionality")

print("\nAfter running this fix, the search should work correctly!")
print("\nIf you still have issues, you may also need to run:")
print("railway run python backend/scripts/apply_fulltext_indexes.py")