"""Search quality metrics and logging service."""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from collections import defaultdict

from app.services.query_parser import query_parser

logger = logging.getLogger(__name__)


class SearchMetrics:
    """Collect and analyze search quality metrics."""
    
    def __init__(self):
        self.search_history = []
        self.skill_match_stats = defaultdict(int)
        
    def log_search(
        self, 
        query: str, 
        results: List[Tuple[dict, float]], 
        search_time: float,
        search_type: str = "vector"
    ) -> Dict[str, Any]:
        """Log a search query and analyze its quality.
        
        Args:
            query: The search query
            results: List of (resume_data, score) tuples
            search_time: Time taken for search in seconds
            search_type: Type of search performed (vector or keyword)
            
        Returns:
            Metrics dictionary with quality analysis
        """
        # Parse the query
        parsed_query = query_parser.parse_query(query)
        required_skills = parsed_query["skills"]
        
        # Analyze results
        metrics = {
            "query": query,
            "parsed_query": parsed_query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "search_type": search_type,
            "search_time_ms": search_time * 1000,
            "total_results": len(results),
            "required_skills": required_skills,
            "skill_match_analysis": [],
            "quality_score": 0.0,
            "issues": []
        }
        
        if not results:
            metrics["issues"].append("No results found")
            self.search_history.append(metrics)
            return metrics
        
        # Analyze skill matches for top results
        perfect_matches = 0
        partial_matches = 0
        no_matches = 0
        
        for i, (resume, score) in enumerate(results[:10]):  # Analyze top 10
            resume_skills = [s.lower() for s in (resume.get("skills", []) or [])]
            
            if required_skills:
                matched_skills = []
                missing_skills = []
                
                for skill in required_skills:
                    if any(skill in rs for rs in resume_skills):
                        matched_skills.append(skill)
                    else:
                        missing_skills.append(skill)
                
                match_ratio = len(matched_skills) / len(required_skills)
                
                skill_analysis = {
                    "rank": i + 1,
                    "name": f"{resume.get('first_name', '')} {resume.get('last_name', '')}",
                    "score": score,
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "match_ratio": match_ratio,
                    "has_all_skills": len(missing_skills) == 0
                }
                
                metrics["skill_match_analysis"].append(skill_analysis)
                
                # Count match types
                if match_ratio == 1.0:
                    perfect_matches += 1
                elif match_ratio > 0:
                    partial_matches += 1
                else:
                    no_matches += 1
                    
                # Log issues
                if i < 3 and match_ratio < 1.0:  # Top 3 should have all skills
                    metrics["issues"].append(
                        f"Rank {i+1} missing skills: {', '.join(missing_skills)}"
                    )
        
        # Calculate quality score
        if required_skills:
            # Quality factors:
            # 1. Top 3 results should have all required skills
            top_3_perfect = sum(1 for a in metrics["skill_match_analysis"][:3] 
                              if a["match_ratio"] == 1.0)
            
            # 2. Overall skill match ratio in top 10
            avg_match_ratio = sum(a["match_ratio"] for a in metrics["skill_match_analysis"]) / len(metrics["skill_match_analysis"]) if metrics["skill_match_analysis"] else 0
            
            # 3. Search speed (bonus if under 500ms)
            speed_bonus = 0.1 if metrics["search_time_ms"] < 500 else 0
            
            # Calculate final score (0-1)
            quality_score = (
                (top_3_perfect / 3) * 0.5 +  # 50% weight on top 3 having all skills
                avg_match_ratio * 0.4 +       # 40% weight on overall match ratio
                speed_bonus                   # 10% bonus for speed
            )
            
            metrics["quality_score"] = round(quality_score, 3)
            
            # Summary stats
            metrics["skill_match_summary"] = {
                "perfect_matches": perfect_matches,
                "partial_matches": partial_matches,
                "no_matches": no_matches,
                "avg_match_ratio": round(avg_match_ratio, 3)
            }
            
            # Update global stats
            self.skill_match_stats["total_searches"] += 1
            self.skill_match_stats["perfect_match_searches"] += 1 if top_3_perfect == 3 else 0
            self.skill_match_stats["total_quality_score"] += quality_score
        
        # Store in history
        self.search_history.append(metrics)
        
        # Log summary
        logger.info(f"Search Quality Metrics for '{query}':")
        logger.info(f"  - Quality Score: {metrics['quality_score']}")
        logger.info(f"  - Search Time: {metrics['search_time_ms']:.1f}ms")
        logger.info(f"  - Results: {metrics['total_results']}")
        
        if required_skills:
            logger.info(f"  - Required Skills: {', '.join(required_skills)}")
            logger.info(f"  - Perfect Matches: {perfect_matches}/10")
            logger.info(f"  - Avg Match Ratio: {metrics['skill_match_summary']['avg_match_ratio']}")
        
        if metrics["issues"]:
            logger.warning(f"  - Issues: {'; '.join(metrics['issues'])}")
        
        return metrics
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all searches."""
        if not self.search_history:
            return {"message": "No searches logged yet"}
        
        total_searches = len(self.search_history)
        skill_searches = [s for s in self.search_history if s["required_skills"]]
        
        avg_quality = (self.skill_match_stats["total_quality_score"] / 
                      self.skill_match_stats["total_searches"]) if self.skill_match_stats["total_searches"] > 0 else 0
        
        search_times = [s["search_time_ms"] for s in self.search_history]
        
        return {
            "total_searches": total_searches,
            "skill_based_searches": len(skill_searches),
            "avg_quality_score": round(avg_quality, 3),
            "perfect_match_rate": round(
                self.skill_match_stats["perfect_match_searches"] / 
                self.skill_match_stats["total_searches"], 3
            ) if self.skill_match_stats["total_searches"] > 0 else 0,
            "avg_search_time_ms": round(sum(search_times) / len(search_times), 1),
            "fastest_search_ms": round(min(search_times), 1),
            "slowest_search_ms": round(max(search_times), 1),
            "searches_with_issues": sum(1 for s in self.search_history if s["issues"])
        }
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search metrics."""
        return self.search_history[-limit:]
    
    def clear_history(self):
        """Clear search history."""
        self.search_history.clear()
        self.skill_match_stats.clear()


# Singleton instance
search_metrics = SearchMetrics()