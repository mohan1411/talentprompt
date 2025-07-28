"""Test endpoint for typo correction."""

from fastapi import APIRouter, Query
import logging

from app.services.query_parser import query_parser
from app.services.gpt4_query_analyzer import gpt4_analyzer

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/test-typo")
async def test_typo(query: str = Query(..., description="Test query")):
    """Test typo correction directly."""
    print(f"\n[TEST-TYPO ENDPOINT] Called with: '{query}'")
    
    # Test query parser
    parsed = query_parser.parse_query(query)
    
    # Test analyzer
    analysis = await gpt4_analyzer.analyze_query(query, {})
    
    return {
        "query": query,
        "parsed": {
            "corrected_query": parsed.get("corrected_query"),
            "original_query": parsed.get("original_query"),
            "skills": parsed.get("skills", [])
        },
        "analysis": {
            "corrected_query": analysis.get("corrected_query"),
            "original_query": analysis.get("original_query"),
            "primary_skills": analysis.get("primary_skills", [])
        },
        "debug": {
            "has_corrected_in_parsed": "corrected_query" in parsed,
            "has_corrected_in_analysis": "corrected_query" in analysis
        }
    }