#!/usr/bin/env python3
"""Create a temporary dev endpoint to generate tokens for OAuth users."""

import os

# Create a temporary API endpoint file
endpoint_code = '''"""Temporary dev endpoint for OAuth token generation."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from jose import jwt
from uuid import uuid4

from app.core.config import settings
from app.core.deps import get_db
from app.models.user import User

router = APIRouter()

@router.post("/dev/generate-oauth-token")
async def generate_oauth_token(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate token for OAuth user (DEV ONLY - REMOVE IN PRODUCTION)."""
    
    # Check if this is development environment
    if not settings.DEBUG and not os.getenv("ALLOW_DEV_ENDPOINTS"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Get user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {email} not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active")
    
    # Create access token
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user.id),  # Use user ID, not email, to match production behavior
        "user_id": str(user.id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4())
    }
    
    access_token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active
        },
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }
'''

print("Creating temporary dev endpoint...")

# Save the endpoint file
endpoint_path = os.path.join("..", "app", "api", "v1", "endpoints", "dev_oauth.py")
os.makedirs(os.path.dirname(endpoint_path), exist_ok=True)

with open(endpoint_path, 'w') as f:
    f.write(endpoint_code)

print(f"✓ Created {endpoint_path}")

# Now update the API router to include this endpoint
print("\nTo use this endpoint:")
print("1. Add this line to app/api/v1/api.py:")
print('   from app.api.v1.endpoints import dev_oauth')
print('   api_router.include_router(dev_oauth.router, prefix="/auth", tags=["dev"])')
print("\n2. Restart your backend server")
print("\n3. Use this curl command:")
print('   curl -X POST "http://localhost:8001/api/v1/auth/dev/generate-oauth-token?email=promtitude@gmail.com"')
print("\n4. Or in browser console:")
print('''   fetch('http://localhost:8001/api/v1/auth/dev/generate-oauth-token?email=promtitude@gmail.com', {method: 'POST'})
     .then(r => r.json())
     .then(data => {
       localStorage.setItem('access_token', data.access_token);
       console.log('Token set! Reloading...');
       location.reload();
     });''')
print("\n⚠️  Remember to remove this endpoint before deploying to production!")