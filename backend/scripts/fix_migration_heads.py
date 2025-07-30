#!/usr/bin/env python3
"""Fix multiple heads issue for production deployment."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

print("Migration Heads Fix Script")
print("=" * 50)

# Show the current migration chain
migrations = [
    ("001_initial_migration", None),
    ("add_email_verification_fields", "001_initial_migration"),
    ("add_fulltext_search", "add_email_verification_fields"),
    ("add_import_queue", "add_fulltext_search"),
    ("add_outreach_tables", "add_import_queue"),
    ("add_analytics_events", "add_outreach_tables"),
    ("oauth_fields_001", "add_analytics_events"),
    ("add_interview_mode_fields", "oauth_fields_001"),
    ("fix_linkedin_url_constraint", "add_interview_mode_fields"),
    ("add_candidate_submissions", "fix_linkedin_url_constraint"),
    ("make_password_nullable", "add_candidate_submissions"),
]

print("\n📋 Current Migration Chain:")
print("-" * 50)
for i, (rev, down) in enumerate(migrations, 1):
    if down:
        print(f"{i}. {rev} → {down}")
    else:
        print(f"{i}. {rev} (root)")

print("\n✅ This creates a single linear chain with one head: make_password_nullable")

print("\n🔧 To run migrations on production:")
print("-" * 50)
print("Option 1: Upgrade all migrations at once")
print("  alembic upgrade heads")
print("\nOption 2: Upgrade to specific revision")
print("  alembic upgrade make_password_nullable")
print("\nOption 3: If still having issues, upgrade step by step:")
print("  alembic upgrade 001_initial_migration")
print("  alembic upgrade add_email_verification_fields")
print("  alembic upgrade add_fulltext_search")
print("  alembic upgrade add_import_queue")
print("  alembic upgrade add_outreach_tables")
print("  alembic upgrade add_analytics_events")
print("  alembic upgrade oauth_fields_001")
print("  alembic upgrade add_interview_mode_fields")
print("  alembic upgrade fix_linkedin_url_constraint")
print("  alembic upgrade add_candidate_submissions")
print("  alembic upgrade make_password_nullable")

print("\n💡 Quick Railway Command:")
print("-" * 50)
print("railway run -s <backend-service> alembic upgrade heads")