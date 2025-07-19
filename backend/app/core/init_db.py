"""Database initialization utilities."""
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine


async def create_outreach_tables(db: AsyncSession) -> dict:
    """Create outreach tables if they don't exist."""
    results = {
        "status": "starting",
        "tables_before": [],
        "tables_after": [],
        "created": False,
        "error": None
    }
    
    try:
        # Check existing tables
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        results["tables_before"] = [row[0] for row in result.fetchall()]
        
        # Check if outreach tables already exist
        outreach_exists = any(t in results["tables_before"] for t in ['outreach_messages', 'outreach_templates'])
        
        if not outreach_exists:
            # Read SQL file
            sql_file = os.path.join(os.path.dirname(__file__), "../../create_outreach_tables.sql")
            with open(sql_file, "r") as f:
                sql_content = f.read()
            
            # Execute SQL statements
            # Split by semicolons but be careful with DO blocks
            statements = []
            current_statement = []
            in_do_block = False
            
            for line in sql_content.split('\n'):
                if line.strip().upper().startswith('DO $$'):
                    in_do_block = True
                
                current_statement.append(line)
                
                if in_do_block and line.strip().endswith('$$;'):
                    in_do_block = False
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                elif not in_do_block and line.strip().endswith(';'):
                    statements.append('\n'.join(current_statement))
                    current_statement = []
            
            # Execute each statement
            for stmt in statements:
                if stmt.strip():
                    await db.execute(text(stmt))
            
            await db.commit()
            results["created"] = True
        
        # Check tables after
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        results["tables_after"] = [row[0] for row in result.fetchall()]
        
        # Verify outreach tables exist
        outreach_tables = ['outreach_messages', 'outreach_templates']
        if all(t in results["tables_after"] for t in outreach_tables):
            results["status"] = "success"
        else:
            results["status"] = "partial"
            results["error"] = "Some tables may not have been created"
            
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        await db.rollback()
    
    return results


async def init_db():
    """Initialize database on startup."""
    async with engine.begin() as conn:
        # Create an AsyncSession
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(conn) as session:
            result = await create_outreach_tables(session)
            print(f"Database initialization result: {result}")
            return result