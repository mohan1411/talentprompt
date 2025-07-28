"""Debug endpoint to test analytics services."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps

router = APIRouter()


@router.get("/test-analytics")
async def test_analytics(
    db: AsyncSession = Depends(deps.get_db)
):
    """Test if analytics services are working."""
    
    result = {
        "imports": {},
        "calculations": {}
    }
    
    # Test imports
    try:
        from app.services.candidate_analytics import candidate_analytics_service
        result["imports"]["candidate_analytics"] = "✅ Success"
    except Exception as e:
        result["imports"]["candidate_analytics"] = f"❌ Error: {str(e)}"
    
    try:
        from app.services.career_dna import career_dna_service
        result["imports"]["career_dna"] = "✅ Success"
    except Exception as e:
        result["imports"]["career_dna"] = f"❌ Error: {str(e)}"
    
    # Test calculations with dummy data
    test_resume = {
        'id': 'test-123',
        'first_name': 'Test',
        'last_name': 'User',
        'current_title': 'Senior Python Developer',
        'years_experience': 8,
        'skills': ['Python', 'AWS', 'Django'],
        'summary': 'Experienced developer',
        'positions': []
    }
    
    if 'candidate_analytics_service' in locals():
        try:
            availability = candidate_analytics_service.calculate_availability_score(test_resume)
            result["calculations"]["availability_score"] = f"✅ {availability:.2f}"
        except Exception as e:
            result["calculations"]["availability_score"] = f"❌ Error: {str(e)}"
        
        try:
            learning = candidate_analytics_service.calculate_learning_velocity(test_resume)
            result["calculations"]["learning_velocity"] = f"✅ {learning:.2f}"
        except Exception as e:
            result["calculations"]["learning_velocity"] = f"❌ Error: {str(e)}"
    
    if 'career_dna_service' in locals():
        try:
            dna = career_dna_service.extract_career_dna(test_resume)
            result["calculations"]["career_dna"] = f"✅ Pattern: {dna['pattern_type']}"
        except Exception as e:
            result["calculations"]["career_dna"] = f"❌ Error: {str(e)}"
    
    return result