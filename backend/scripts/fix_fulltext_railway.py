#!/usr/bin/env python3
"""Fix full-text search configuration via Railway CLI."""

import os
import sys

print("="*60)
print("RAILWAY DATABASE FIX INSTRUCTIONS")
print("="*60)

print("\nTo fix the full-text search indexes in production:")
print("\n1. First, enter the Railway shell:")
print("   railway shell")

print("\n2. Once in the Railway shell, run:")
print("   cd backend")
print("   python scripts/fix_fulltext_columns.py")

print("\n3. The script will:")
print("   - Check your database columns")
print("   - Drop any problematic indexes")
print("   - Create correct indexes for search")

print("\nAlternatively, you can run it directly with:")
print("   railway shell -c \"cd backend && python scripts/fix_fulltext_columns.py\"")

print("\nIf you're still getting connection errors, try:")
print("   railway link")
print("   railway up")
print("\nThen retry the commands above.")