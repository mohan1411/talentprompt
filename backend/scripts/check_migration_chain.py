#!/usr/bin/env python3
"""Check Alembic migration chain for issues."""

import os
import re
from pathlib import Path
from collections import defaultdict

def check_migrations():
    """Check all migrations for consistency."""
    versions_dir = Path(__file__).parent.parent / "alembic" / "versions"
    migrations = {}
    
    print("Checking Alembic Migration Chain")
    print("=" * 50)
    
    # Read all migration files
    for file in versions_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
            
        with open(file, 'r') as f:
            content = f.read()
            
        # Extract revision info
        revision_match = re.search(r"revision = '([^']+)'", content)
        down_revision_match = re.search(r"down_revision = ('([^']+)'|None)", content)
        
        if revision_match:
            revision = revision_match.group(1)
            down_revision = down_revision_match.group(2) if down_revision_match.group(2) else None
            
            migrations[revision] = {
                'file': file.name,
                'down_revision': down_revision,
                'content': content[:200]  # First 200 chars for context
            }
    
    # Build the chain
    print("\n📊 Migration Chain:")
    print("-" * 50)
    
    # Find root migrations (down_revision = None)
    roots = [rev for rev, info in migrations.items() if info['down_revision'] is None]
    
    for root in roots:
        print(f"\n🌳 Root: {root} ({migrations[root]['file']})")
        print_chain(migrations, root, indent=1)
    
    # Check for issues
    print("\n\n🔍 Checking for Issues:")
    print("-" * 50)
    
    # Check for missing references
    all_revisions = set(migrations.keys())
    for rev, info in migrations.items():
        if info['down_revision'] and info['down_revision'] not in all_revisions:
            print(f"❌ ERROR: {rev} references non-existent migration: {info['down_revision']}")
    
    # Check for duplicate down_revisions
    down_revs = defaultdict(list)
    for rev, info in migrations.items():
        if info['down_revision']:
            down_revs[info['down_revision']].append(rev)
    
    for down_rev, revs in down_revs.items():
        if len(revs) > 1:
            print(f"⚠️  WARNING: Multiple migrations depend on {down_rev}:")
            for rev in revs:
                print(f"   - {rev} ({migrations[rev]['file']})")
    
    print("\n✅ Chain verification complete!")
    
    # Print the correct order
    print("\n📋 Correct Migration Order:")
    print("-" * 50)
    ordered = get_ordered_migrations(migrations)
    for i, rev in enumerate(ordered, 1):
        print(f"{i}. {rev} ({migrations[rev]['file']})")
        if migrations[rev]['down_revision']:
            print(f"   └─ depends on: {migrations[rev]['down_revision']}")

def print_chain(migrations, current, indent=0):
    """Print migration chain recursively."""
    # Find migrations that depend on current
    dependents = [rev for rev, info in migrations.items() 
                  if info['down_revision'] == current]
    
    for dep in dependents:
        print("  " * indent + f"└─ {dep} ({migrations[dep]['file']})")
        print_chain(migrations, dep, indent + 1)

def get_ordered_migrations(migrations):
    """Get migrations in dependency order."""
    ordered = []
    remaining = dict(migrations)
    
    while remaining:
        # Find migrations with no dependencies or dependencies already in ordered
        ready = []
        for rev, info in remaining.items():
            if info['down_revision'] is None or info['down_revision'] in ordered:
                ready.append(rev)
        
        if not ready:
            print("ERROR: Circular dependency detected!")
            break
        
        # Add ready migrations to ordered list
        for rev in ready:
            ordered.append(rev)
            del remaining[rev]
    
    return ordered

if __name__ == "__main__":
    check_migrations()