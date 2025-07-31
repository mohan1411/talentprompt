import asyncio
import sys
sys.path.append('/mnt/d/Projects/AI/BusinessIdeas/SmallBusiness/TalentPrompt/backend')
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.user import User
from app.core.config import settings

async def check_oauth_users():
    engine = create_async_engine(settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find OAuth users
        result = await session.execute(
            select(User).where(User.oauth_provider != None)
        )
        oauth_users = result.scalars().all()
        
        print(f"Found {len(oauth_users)} OAuth users:")
        for user in oauth_users:
            print(f"- {user.email} (provider: {user.oauth_provider}, id: {user.id})")
        
        # Also check promtitude gmail
        result = await session.execute(
            select(User).where(User.email == "promtitude@gmail.com")
        )
        promtitude_user = result.scalar_one_or_none()
        if promtitude_user:
            print(f"\nPromtitude user found: {promtitude_user.email} (provider: {promtitude_user.oauth_provider})")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_oauth_users())