"""
Career DNA Matching Service

Analyzes career trajectories and patterns to find candidates with similar "DNA"
to your top performers or specific career paths.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


class CareerDNAService:
    """Service for analyzing and matching career trajectories."""
    
    def __init__(self):
        # Career progression patterns
        self.progression_patterns = {
            'fast_track': {
                'description': 'Rapid advancement through roles',
                'indicators': ['promoted within 2 years', 'skip levels', 'early leadership'],
                'typical_timeline': [
                    ('entry', 0, 2),
                    ('mid', 2, 4),
                    ('senior', 4, 7),
                    ('lead', 7, 10)
                ]
            },
            'deep_specialist': {
                'description': 'Deep expertise in specific domain',
                'indicators': ['same role type', 'skill deepening', 'thought leadership'],
                'typical_timeline': [
                    ('junior specialist', 0, 3),
                    ('specialist', 3, 6),
                    ('senior specialist', 6, 10),
                    ('principal specialist', 10, 15)
                ]
            },
            'lateral_explorer': {
                'description': 'Cross-functional experience builder',
                'indicators': ['role variety', 'industry changes', 'adaptability'],
                'typical_timeline': [
                    ('role A', 0, 3),
                    ('role B', 3, 6),
                    ('role C', 6, 9),
                    ('integrated role', 9, 12)
                ]
            },
            'startup_builder': {
                'description': 'Entrepreneurial and high-growth focused',
                'indicators': ['startup experience', 'wearing many hats', 'rapid scaling'],
                'typical_timeline': [
                    ('early employee', 0, 2),
                    ('team lead', 2, 4),
                    ('founder/co-founder', 4, 8)
                ]
            },
            'corporate_climber': {
                'description': 'Traditional corporate advancement',
                'indicators': ['large companies', 'structured progression', 'MBA'],
                'typical_timeline': [
                    ('analyst', 0, 3),
                    ('senior analyst', 3, 5),
                    ('manager', 5, 8),
                    ('senior manager', 8, 12),
                    ('director', 12, 15)
                ]
            }
        }
        
        # Skills evolution patterns
        self.skill_evolution_patterns = {
            'T-shaped': 'Deep expertise in one area with broad knowledge',
            'Pi-shaped': 'Deep expertise in two complementary areas',
            'Comb-shaped': 'Multiple areas of depth',
            'Generalist': 'Broad knowledge across many areas'
        }
    
    def extract_career_dna(self, resume_data: Dict) -> Dict:
        """
        Extract the career DNA profile from a candidate's resume.
        
        Returns:
            Dictionary containing career DNA profile
        """
        dna_profile = {
            'pattern_type': 'unknown',
            'progression_speed': 0.5,  # 0-1 scale
            'skill_evolution': 'unknown',
            'key_transitions': [],
            'growth_indicators': [],
            'DNA_vector': [],  # Numerical representation for matching
            'strengths': [],
            'unique_traits': []
        }
        
        # Analyze career progression pattern
        pattern = self._identify_progression_pattern(resume_data)
        dna_profile['pattern_type'] = pattern
        
        # Calculate progression speed
        dna_profile['progression_speed'] = self._calculate_progression_speed(resume_data)
        
        # Analyze skill evolution
        dna_profile['skill_evolution'] = self._analyze_skill_evolution(resume_data)
        
        # Identify key career transitions
        dna_profile['key_transitions'] = self._identify_key_transitions(resume_data)
        
        # Extract growth indicators
        dna_profile['growth_indicators'] = self._extract_growth_indicators(resume_data)
        
        # Generate DNA vector for similarity matching
        dna_profile['DNA_vector'] = self._generate_dna_vector(dna_profile)
        
        # Identify unique strengths and traits
        dna_profile['strengths'] = self._identify_strengths(resume_data)
        dna_profile['unique_traits'] = self._identify_unique_traits(resume_data)
        
        return dna_profile
    
    def calculate_dna_similarity(self, dna1: Dict, dna2: Dict) -> float:
        """
        Calculate similarity between two career DNA profiles.
        
        Returns:
            Similarity score between 0 and 1
        """
        if not dna1.get('DNA_vector') or not dna2.get('DNA_vector'):
            return 0.0
        
        # Calculate cosine similarity between DNA vectors without numpy
        vector1 = dna1['DNA_vector']
        vector2 = dna2['DNA_vector']
        
        # Ensure vectors are same length
        if len(vector1) != len(vector2):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        
        # Calculate norms
        norm1 = math.sqrt(sum(a * a for a in vector1))
        norm2 = math.sqrt(sum(b * b for b in vector2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Boost similarity for matching pattern types
        if dna1['pattern_type'] == dna2['pattern_type']:
            similarity = min(1.0, similarity + 0.1)
        
        return float(similarity)
    
    def find_similar_careers(self, target_dna: Dict, candidate_dnas: List[Tuple[str, Dict]], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find candidates with similar career DNA.
        
        Args:
            target_dna: Target career DNA profile
            candidate_dnas: List of (candidate_id, dna_profile) tuples
            top_k: Number of top matches to return
            
        Returns:
            List of (candidate_id, similarity_score) tuples
        """
        similarities = []
        
        for candidate_id, candidate_dna in candidate_dnas:
            similarity = self.calculate_dna_similarity(target_dna, candidate_dna)
            similarities.append((candidate_id, similarity))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def _identify_progression_pattern(self, resume_data: Dict) -> str:
        """Identify the career progression pattern."""
        positions = resume_data.get('positions', [])
        if not positions:
            return 'unknown'
        
        # Analyze position changes
        role_types = set()
        companies = set()
        time_in_roles = []
        
        for i, position in enumerate(positions):
            role_type = self._extract_role_type(position.get('title', ''))
            role_types.add(role_type)
            companies.add(position.get('company', ''))
            
            # Calculate time in role (simplified)
            if i < len(positions) - 1:
                time_in_roles.append(2)  # Placeholder - would calculate actual duration
        
        # Determine pattern based on indicators
        if len(role_types) == 1 and len(companies) <= 2:
            return 'deep_specialist'
        elif len(role_types) >= 4:
            return 'lateral_explorer'
        elif any('startup' in str(c).lower() for c in companies):
            return 'startup_builder'
        elif len(companies) >= 1 and all(t < 3 for t in time_in_roles[:3]):
            return 'fast_track'
        else:
            return 'corporate_climber'
    
    def _calculate_progression_speed(self, resume_data: Dict) -> float:
        """Calculate how quickly the candidate has progressed."""
        years_exp = resume_data.get('years_experience', 0)
        current_level = self._determine_seniority_level(resume_data.get('current_title', ''))
        
        if years_exp == 0:
            return 0.5
        
        # Score based on reaching level relative to years
        level_typical_years = {
            'executive': 15,
            'lead': 10,
            'senior': 6,
            'mid': 3,
            'junior': 0
        }
        
        typical_years = level_typical_years.get(current_level, 5)
        if years_exp < typical_years:
            # Faster than typical
            return min(1.0, 0.5 + (typical_years - years_exp) / typical_years * 0.5)
        else:
            # Slower than typical
            return max(0.0, 0.5 - (years_exp - typical_years) / typical_years * 0.3)
    
    def _analyze_skill_evolution(self, resume_data: Dict) -> str:
        """Analyze how skills have evolved."""
        skills = resume_data.get('skills', [])
        
        if not skills:
            return 'unknown'
        
        # Categorize skills
        skill_categories = defaultdict(int)
        for skill in skills:
            category = self._categorize_skill(skill)
            skill_categories[category] += 1
        
        # Determine pattern
        deep_categories = sum(1 for count in skill_categories.values() if count >= 5)
        broad_categories = len(skill_categories)
        
        if deep_categories >= 2:
            return 'Pi-shaped'
        elif deep_categories == 1 and broad_categories >= 3:
            return 'T-shaped'
        elif deep_categories >= 3:
            return 'Comb-shaped'
        else:
            return 'Generalist'
    
    def _identify_key_transitions(self, resume_data: Dict) -> List[Dict]:
        """Identify significant career transitions."""
        transitions = []
        positions = resume_data.get('positions', [])
        
        for i in range(1, len(positions)):
            prev = positions[i]
            curr = positions[i-1]
            
            # Check for significant transitions
            prev_level = self._determine_seniority_level(prev.get('title', ''))
            curr_level = self._determine_seniority_level(curr.get('title', ''))
            
            if prev_level != curr_level:
                transitions.append({
                    'type': 'level_change',
                    'from': prev_level,
                    'to': curr_level,
                    'description': f"{prev.get('title')} → {curr.get('title')}"
                })
        
        return transitions
    
    def _extract_growth_indicators(self, resume_data: Dict) -> List[str]:
        """Extract indicators of career growth."""
        indicators = []
        
        # Check for leadership progression
        if any('lead' in str(p.get('title', '')).lower() for p in resume_data.get('positions', [])):
            indicators.append('leadership_growth')
        
        # Check for technical depth
        if len(resume_data.get('skills', [])) > 20:
            indicators.append('technical_depth')
        
        # Check for certifications
        if resume_data.get('certifications'):
            indicators.append('continuous_learning')
        
        return indicators
    
    def _generate_dna_vector(self, dna_profile: Dict) -> List[float]:
        """Generate numerical vector representation of career DNA."""
        vector = []
        
        # Pattern type encoding (one-hot)
        patterns = ['fast_track', 'deep_specialist', 'lateral_explorer', 'startup_builder', 'corporate_climber']
        for pattern in patterns:
            vector.append(1.0 if dna_profile['pattern_type'] == pattern else 0.0)
        
        # Progression speed
        vector.append(dna_profile['progression_speed'])
        
        # Skill evolution encoding
        skill_patterns = ['T-shaped', 'Pi-shaped', 'Comb-shaped', 'Generalist']
        for pattern in skill_patterns:
            vector.append(1.0 if dna_profile['skill_evolution'] == pattern else 0.0)
        
        # Growth indicators
        indicators = ['leadership_growth', 'technical_depth', 'continuous_learning']
        for indicator in indicators:
            vector.append(1.0 if indicator in dna_profile['growth_indicators'] else 0.0)
        
        # Number of transitions
        vector.append(min(1.0, len(dna_profile['key_transitions']) / 5.0))
        
        return vector
    
    def _identify_strengths(self, resume_data: Dict) -> List[str]:
        """Identify key strengths from career data."""
        strengths = []
        
        # Quick progression
        if resume_data.get('years_experience', 0) < 10 and 'senior' in resume_data.get('current_title', '').lower():
            strengths.append('rapid_advancement')
        
        # Diverse skills
        if len(set(resume_data.get('skills', []))) > 15:
            strengths.append('versatile_skillset')
        
        # Stability
        positions = resume_data.get('positions', [])
        if positions and all(self._estimate_tenure(p) > 2 for p in positions[:3]):
            strengths.append('commitment_stability')
        
        return strengths
    
    def _identify_unique_traits(self, resume_data: Dict) -> List[str]:
        """Identify unique or rare traits."""
        traits = []
        
        # Unique combinations
        skills = set(s.lower() for s in resume_data.get('skills', []))
        
        # Technical + Leadership
        if any(s in skills for s in ['python', 'java', 'react']) and any(s in skills for s in ['leadership', 'management']):
            traits.append('technical_leader')
        
        # Cross-industry experience
        industries = set(p.get('industry', '') for p in resume_data.get('positions', []))
        if len(industries) >= 3:
            traits.append('cross_industry_expertise')
        
        return traits
    
    def _extract_role_type(self, title: str) -> str:
        """Extract general role type from title."""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ['engineer', 'developer', 'architect']):
            return 'technical'
        elif any(x in title_lower for x in ['manager', 'director', 'vp']):
            return 'management'
        elif any(x in title_lower for x in ['analyst', 'scientist']):
            return 'analytical'
        else:
            return 'other'
    
    def _determine_seniority_level(self, title: str) -> str:
        """Determine seniority level from title."""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ['cto', 'ceo', 'vp', 'director']):
            return 'executive'
        elif any(x in title_lower for x in ['lead', 'principal', 'staff']):
            return 'lead'
        elif 'senior' in title_lower:
            return 'senior'
        elif any(x in title_lower for x in ['junior', 'entry']):
            return 'junior'
        else:
            return 'mid'
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill into broad categories."""
        skill_lower = skill.lower()
        
        if any(x in skill_lower for x in ['python', 'java', 'javascript', 'react', 'node']):
            return 'programming'
        elif any(x in skill_lower for x in ['aws', 'azure', 'gcp', 'docker', 'kubernetes']):
            return 'cloud_devops'
        elif any(x in skill_lower for x in ['machine learning', 'ai', 'deep learning']):
            return 'ai_ml'
        elif any(x in skill_lower for x in ['leadership', 'management', 'agile']):
            return 'soft_skills'
        else:
            return 'other'
    
    def _estimate_tenure(self, position: Dict) -> float:
        """Estimate tenure at a position in years."""
        # Simplified - in production would calculate from dates
        return 2.5


# Singleton instance
career_dna_service = CareerDNAService()