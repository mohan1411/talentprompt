"""
Candidate Analytics Service

Analyzes candidates to calculate:
- Availability likelihood based on profile indicators
- Learning velocity from career progression
- Career trajectory patterns
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from collections import defaultdict

class CandidateAnalyticsService:
    """Service for analyzing candidate metrics beyond basic matching."""
    
    def __init__(self):
        # Indicators that suggest a candidate might be open to opportunities
        self.availability_indicators = {
            'positive': [
                'looking for', 'seeking', 'open to', 'available',
                'freelance', 'consultant', 'contract', 'interim',
                'recently completed', 'just finished', 'concluding'
            ],
            'negative': [
                'not looking', 'happy where', 'recently joined',
                'just started', 'promoted to', 'leading', 'building'
            ]
        }
        
        # Job title progressions that indicate fast learning
        self.career_progressions = {
            'junior_to_senior': [
                ('junior', 'senior'),
                ('associate', 'lead'),
                ('analyst', 'manager'),
                ('developer', 'architect'),
                ('engineer', 'principal')
            ],
            'ic_to_leadership': [
                ('developer', 'lead'),
                ('engineer', 'manager'),
                ('analyst', 'director'),
                ('specialist', 'head of')
            ]
        }
    
    def calculate_availability_score(self, resume_data: Dict) -> float:
        """
        Calculate likelihood that a candidate is available (0.0 to 1.0).
        
        Factors considered:
        - Keywords in summary/bio
        - Time at current position
        - Recent activity patterns
        - Employment gaps
        """
        score = 0.5  # Start neutral
        
        # Check summary/bio for indicators
        summary = (resume_data.get('summary', '') + ' ' + 
                  resume_data.get('bio', '')).lower()
        
        for indicator in self.availability_indicators['positive']:
            if indicator in summary:
                score += 0.1
        
        for indicator in self.availability_indicators['negative']:
            if indicator in summary:
                score -= 0.1
        
        # Check time at current position
        current_position_duration = self._get_current_position_duration(resume_data)
        if current_position_duration:
            if current_position_duration < 365:  # Less than 1 year
                score -= 0.2  # Recently started, less likely to move
            elif current_position_duration > 730:  # More than 2 years
                score += 0.1  # Might be ready for change
            elif current_position_duration > 1460:  # More than 4 years
                score += 0.2  # More likely to be open
        
        # Check for employment gaps (might indicate active searching)
        if self._has_recent_employment_gap(resume_data):
            score += 0.2
        
        # Check if contractor/freelancer (usually more available)
        if self._is_contractor(resume_data):
            score += 0.3
        
        # Ensure score stays within bounds
        return max(0.0, min(1.0, score))
    
    def calculate_learning_velocity(self, resume_data: Dict) -> float:
        """
        Calculate how quickly the candidate learns and progresses (0.0 to 1.0).
        
        Factors considered:
        - Speed of career progression
        - Diversity of skills acquired
        - Number of technologies mastered
        - Certifications and continuous learning
        """
        score = 0.5  # Start neutral
        
        # Analyze career progression speed
        progression_score = self._analyze_career_progression(resume_data)
        score += progression_score * 0.3
        
        # Check skill diversity
        skills = resume_data.get('skills', [])
        if len(skills) > 20:
            score += 0.2
        elif len(skills) > 10:
            score += 0.1
        
        # Check for certifications (indicates continuous learning)
        if resume_data.get('certifications'):
            score += 0.1 * min(len(resume_data['certifications']), 3)
        
        # Check for recent skill additions
        if self._has_recent_skills(resume_data):
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def analyze_career_trajectory(self, resume_data: Dict) -> Dict:
        """
        Analyze the candidate's career trajectory pattern.
        
        Returns:
            Dictionary with trajectory insights
        """
        trajectory = {
            'pattern': 'steady',  # steady, fast-growth, lateral, specialist, generalist
            'current_level': 'mid',  # junior, mid, senior, lead, executive
            'years_to_current': 0,
            'role_changes': 0,
            'industry_changes': 0,
            'is_ascending': True
        }
        
        # Analyze job history
        positions = resume_data.get('positions', [])
        if not positions:
            return trajectory
        
        # Determine current level
        current_title = resume_data.get('current_title', '').lower()
        trajectory['current_level'] = self._determine_seniority_level(current_title)
        
        # Calculate years to reach current level
        years_experience = resume_data.get('years_experience', 0)
        trajectory['years_to_current'] = years_experience
        
        # Count role and industry changes
        previous_role = None
        previous_industry = None
        for position in positions:
            role = self._extract_role_type(position.get('title', ''))
            industry = position.get('industry', 'unknown')
            
            if previous_role and role != previous_role:
                trajectory['role_changes'] += 1
            if previous_industry and industry != previous_industry:
                trajectory['industry_changes'] += 1
            
            previous_role = role
            previous_industry = industry
        
        # Determine pattern
        if trajectory['role_changes'] > len(positions) * 0.6:
            trajectory['pattern'] = 'generalist'
        elif trajectory['role_changes'] < len(positions) * 0.2:
            trajectory['pattern'] = 'specialist'
        elif years_experience > 0 and trajectory['years_to_current'] / years_experience < 0.7:
            trajectory['pattern'] = 'fast-growth'
        elif trajectory['industry_changes'] > 2:
            trajectory['pattern'] = 'lateral'
        
        return trajectory
    
    def _get_current_position_duration(self, resume_data: Dict) -> Optional[int]:
        """Get duration in days at current position."""
        positions = resume_data.get('positions', [])
        if not positions:
            return None
        
        current_position = positions[0]  # Assuming first is current
        start_date = current_position.get('start_date')
        if not start_date:
            return None
        
        # Simple date parsing (in production, use proper date parsing)
        try:
            if isinstance(start_date, str):
                # Assume format like "2022-01-01"
                start = datetime.strptime(start_date[:10], '%Y-%m-%d')
            else:
                start = start_date
            
            return (datetime.now() - start).days
        except:
            return None
    
    def _has_recent_employment_gap(self, resume_data: Dict) -> bool:
        """Check if there's a recent employment gap."""
        positions = resume_data.get('positions', [])
        if len(positions) < 2:
            return False
        
        # Check gap between two most recent positions
        # Simplified - in production would need proper date handling
        return False  # Placeholder
    
    def _is_contractor(self, resume_data: Dict) -> bool:
        """Check if candidate is a contractor/freelancer."""
        current_title = resume_data.get('current_title', '').lower()
        contractor_keywords = ['contractor', 'freelance', 'consultant', 'consulting']
        return any(keyword in current_title for keyword in contractor_keywords)
    
    def _analyze_career_progression(self, resume_data: Dict) -> float:
        """Analyze speed of career progression."""
        years_exp = resume_data.get('years_experience', 0)
        if years_exp == 0:
            return 0.5
        
        current_level = self._determine_seniority_level(
            resume_data.get('current_title', '')
        )
        
        # Score based on reaching level relative to years
        level_scores = {
            'executive': (10, 1.0),  # (typical_years, max_score)
            'lead': (7, 0.8),
            'senior': (5, 0.6),
            'mid': (3, 0.4),
            'junior': (0, 0.2)
        }
        
        typical_years, max_score = level_scores.get(current_level, (5, 0.5))
        if years_exp < typical_years:
            # Reached level faster than typical
            return max_score
        else:
            # Adjust score based on how much longer it took
            delay_factor = (years_exp - typical_years) / typical_years
            return max(0.2, max_score - (delay_factor * 0.2))
    
    def _has_recent_skills(self, resume_data: Dict) -> bool:
        """Check if candidate has been learning new skills recently."""
        # In production, would analyze skill timestamps or recent projects
        skills = resume_data.get('skills', [])
        modern_skills = ['kubernetes', 'terraform', 'react hooks', 'gpt-4', 
                         'langchain', 'rust', 'go', 'flutter', 'fastapi']
        
        return any(skill.lower() in modern_skills for skill in skills)
    
    def _determine_seniority_level(self, title: str) -> str:
        """Determine seniority level from job title."""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ['cto', 'ceo', 'vp', 'director', 'head of']):
            return 'executive'
        elif any(x in title_lower for x in ['lead', 'principal', 'staff', 'architect']):
            return 'lead'
        elif 'senior' in title_lower:
            return 'senior'
        elif any(x in title_lower for x in ['junior', 'entry', 'intern']):
            return 'junior'
        else:
            return 'mid'
    
    def _extract_role_type(self, title: str) -> str:
        """Extract general role type from title."""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ['engineer', 'developer', 'programmer']):
            return 'engineering'
        elif any(x in title_lower for x in ['manager', 'lead', 'director']):
            return 'management'
        elif any(x in title_lower for x in ['designer', 'ux', 'ui']):
            return 'design'
        elif any(x in title_lower for x in ['analyst', 'scientist', 'researcher']):
            return 'analytics'
        elif any(x in title_lower for x in ['sales', 'account', 'business development']):
            return 'sales'
        else:
            return 'other'


# Singleton instance
candidate_analytics_service = CandidateAnalyticsService()