#!/usr/bin/env python3
"""Fix interview_sessions table schema - ensure all columns exist."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.models.interview import InterviewSession
from sqlalchemy.schema import CreateTable


def get_model_columns():
    """Get all columns defined in the InterviewSession model."""
    return {
        column.name: {
            'type': str(column.type),
            'nullable': column.nullable,
            'default': column.default
        }
        for column in InterviewSession.__table__.columns
    }


def get_database_columns(engine):
    """Get all columns that exist in the database."""
    inspector = inspect(engine)
    columns = inspector.get_columns('interview_sessions')
    return {col['name']: col for col in columns}


def fix_missing_columns():
    """Check and add any missing columns to the interview_sessions table."""
    
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    print("Analyzing interview_sessions table schema...")
    
    # Get columns from model and database
    model_columns = get_model_columns()
    db_columns = get_database_columns(engine)
    
    # Find missing columns
    missing_columns = set(model_columns.keys()) - set(db_columns.keys())
    
    if not missing_columns:
        print("✓ All columns exist in the database")
        return
    
    print(f"\n❌ Found {len(missing_columns)} missing columns:")
    for col in missing_columns:
        print(f"  - {col}")
    
    # Add missing columns
    print("\nAdding missing columns...")
    
    with engine.connect() as conn:
        for column_name in missing_columns:
            column_info = model_columns[column_name]
            
            # Map SQLAlchemy types to PostgreSQL types
            type_mapping = {
                'VARCHAR': 'VARCHAR',
                'TEXT': 'TEXT',
                'INTEGER': 'INTEGER',
                'FLOAT': 'FLOAT',
                'DATETIME': 'TIMESTAMP',
                'JSON': 'JSON',
                'UUID': 'UUID',
                'BOOLEAN': 'BOOLEAN',
                'Enum': 'VARCHAR',  # Simplified for enums
            }
            
            # Get the SQL type
            sql_type = 'VARCHAR'  # Default
            for sa_type, pg_type in type_mapping.items():
                if sa_type in column_info['type']:
                    sql_type = pg_type
                    break
            
            # Handle UUID type specially
            if 'UUID' in column_info['type']:
                sql_type = 'UUID'
            
            # Build the ALTER TABLE statement
            null_clause = 'NULL' if column_info['nullable'] else 'NOT NULL'
            
            try:
                if column_info['nullable'] or column_info['default'] is not None:
                    # Can add nullable columns or columns with defaults
                    sql = f"""
                        ALTER TABLE interview_sessions 
                        ADD COLUMN {column_name} {sql_type} {null_clause}
                    """
                else:
                    # For NOT NULL columns without defaults, add as nullable first
                    sql = f"""
                        ALTER TABLE interview_sessions 
                        ADD COLUMN {column_name} {sql_type} NULL
                    """
                
                conn.execute(text(sql))
                conn.commit()
                print(f"✓ Added column: {column_name} ({sql_type})")
                
            except Exception as e:
                print(f"✗ Failed to add column {column_name}: {e}")
    
    # Verify all columns now exist
    print("\nVerifying schema...")
    db_columns_after = get_database_columns(engine)
    still_missing = set(model_columns.keys()) - set(db_columns_after.keys())
    
    if not still_missing:
        print("✅ All columns now exist! The interviews page should load without errors.")
    else:
        print(f"❌ Still missing columns: {still_missing}")
        print("\nPlease check your database manually.")


def show_quick_fix():
    """Show the quick SQL fix for the most common issue."""
    print("\n" + "="*60)
    print("QUICK FIX - Run this SQL directly in your database:")
    print("="*60)
    print("""
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interview_category VARCHAR;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interview_type VARCHAR;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS journey_id UUID;
""")
    print("="*60)


if __name__ == "__main__":
    try:
        fix_missing_columns()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        show_quick_fix()
        sys.exit(1)