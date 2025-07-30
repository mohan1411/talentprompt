#!/usr/bin/env python3
"""Check for multiple head migrations."""

import subprocess
import sys

try:
    # Run alembic heads command
    result = subprocess.run(
        ["alembic", "heads"],
        capture_output=True,
        text=True,
        cwd="/mnt/d/Projects/AI/BusinessIdeas/SmallBusiness/TalentPrompt/backend"
    )
    
    print("Alembic Heads Check")
    print("=" * 50)
    
    if result.stdout:
        heads = result.stdout.strip().split('\n')
        print(f"\nFound {len(heads)} head(s):")
        for head in heads:
            print(f"  - {head}")
        
        if len(heads) > 1:
            print("\n⚠️  WARNING: Multiple heads detected!")
            print("This will cause 'alembic upgrade head' to fail.")
            print("\nTo fix, run one of these:")
            print("1. alembic upgrade heads  # Upgrades all heads")
            print("2. alembic merge -m 'merge heads' <head1> <head2>  # Creates merge migration")
        else:
            print("\n✅ Single head found - migrations are linear!")
    
    if result.stderr:
        print(f"\nErrors: {result.stderr}")
        
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure you're in the backend directory and alembic is installed.")