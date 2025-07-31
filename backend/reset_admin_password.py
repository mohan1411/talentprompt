#!/usr/bin/env python3
"""Reset admin user password."""

import asyncio
from sqlalchemy import text
from app.db.session import async_session_maker
from app.core.security import get_password_hash

async def reset_admin_password():
    """Reset admin password to admin123."""
    try:
        async with async_session_maker() as db:
            # Update admin password
            new_password_hash = get_password_hash("admin123")
            
            result = await db.execute(
                text("""
                    UPDATE users 
                    SET hashed_password = :password_hash 
                    WHERE email = 'admin@promtitude.com'
                    RETURNING email, username
                """),
                {"password_hash": new_password_hash}
            )
            
            user = result.fetchone()
            if user:
                await db.commit()
                print(f"✅ Password reset successfully for {user[0]}")
                print(f"   Username: {user[1]}")
                print(f"   New password: admin123")
            else:
                print("❌ Admin user not found!")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Resetting admin password...")
    asyncio.run(reset_admin_password())