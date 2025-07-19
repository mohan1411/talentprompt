#!/usr/bin/env python
"""Check analytics module loading."""

try:
    print("Checking analytics imports...")
    
    # Check models
    from app.models import AnalyticsEvent, EventType
    print("✓ Analytics models imported successfully")
    
    # Check service
    from app.services.analytics import analytics_service
    print("✓ Analytics service imported successfully")
    
    # Check endpoint
    from app.api.v1.endpoints import analytics
    print("✓ Analytics endpoint imported successfully")
    
    # Check API router
    from app.api.v1.api import api_router
    print("✓ API router imported successfully")
    
    print("\nAll analytics modules loaded successfully!")
    
except Exception as e:
    print(f"❌ Error loading analytics: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()