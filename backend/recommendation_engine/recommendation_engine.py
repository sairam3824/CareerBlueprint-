"""
Recommendation Engine Module
Matches user profiles with jobs using semantic similarity and multi-factor scoring
"""

import logging
import numpy as np
from typing import List, Dict, Optional
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates job recommendations based on user profile"""
    
    def __init__(self, skill_analyzer, openai_helper=None):
        self.skill_analyzer = skill_analyzer
        self.openai_helper = openai_helper
        self.weights = {
            "skill_match": 0.5,
            "experience_match": 0.2,
            "location_match": 0.15,
            "salary_match": 0.15
        }
    
    def generate_recommendations(self, user_profile: Dict, jobs: List[Dict], 
                                limit: int = 10) -> List[Dict]:
        """
        Generate ranked job recommendations
        
        Args:
            user_profile: User profile with skills, experience, preferences
            jobs: List of job dictionaries
            limit: Maximum number of recommendations
            
        Returns:
            List of recommendation dictionaries with scores and explanations
        """
        if not jobs:
            return []
        
        recommendations = []
        
        for job in jobs:
            # Compute match score
            score = self.compute_match_score(user_profile, job)
            
            # Get matching and missing skills
            matching_skills, missing_skills = self._compare_skills(
                user_profile.get("skills", []),
                job.get("requirements", [])
            )
            
            # Generate explanation
            explanation = self._generate_explanation(
                score, matching_skills, missing_skills, user_profile, job
            )
            
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(job)
            
            recommendation = {
                "job": job,
                "match_score": round(score, 2),
                "matching_skills": matching_skills,
                "missing_skills": missing_skills,
                "explanation": explanation,
                "confidence": confidence
            }
            
            recommendations.append(recommendation)
        
        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        return recommendations[:limit]
    
    def compute_match_score(self, user_profile: Dict, job: Dict) -> float:
        """
        Compute overall match score (0-100)
        
        Args:
            user_profile: User profile dictionary
            job: Job dictionary
            
        Returns:
            Match score between 0 and 100
        """
        scores = {}
        
        # Skill similarity
        scores["skill_match"] = self._skill_similarity(
            user_profile.get("skills", []),
            job.get("requirements", [])
        )
        
        # Experience match
        scores["experience_match"] = self._experience_match(
            user_profile.get("experience_years", 0),
            job.get("description", "")
        )
        
        # Location match
        scores["location_match"] = self._location_match(
            user_profile.get("preferred_locations", []),
            job.get("location", ""),
            job.get("remote", False)
        )
        
        # Salary match
        scores["salary_match"] = self._salary_match(
            user_profile.get("salary_min"),
            user_profile.get("salary_max"),
            job.get("salary_min"),
            job.get("salary_max")
        )
        
        # Weighted average
        total_score = sum(
            scores[factor] * self.weights[factor]
            for factor in self.weights.keys()
        )
        
        return total_score * 100  # Convert to 0-100 scale
    
    def _skill_similarity(self, user_skills: List[str], job_skills: List[str]) -> float:
        """
        Compute semantic similarity between skill sets
        
        Args:
            user_skills: List of user's skills
            job_skills: List of required skills
            
        Returns:
            Similarity score between 0 and 1
        """
        if not user_skills or not job_skills:
            return 0.0
        
        # Normalize skills
        user_skills_lower = [s.lower() for s in user_skills]
        job_skills_lower = [s.lower() for s in job_skills]
        
        # Simple overlap-based similarity
        matching = set(user_skills_lower) & set(job_skills_lower)
        overlap_score = len(matching) / len(job_skills_lower) if job_skills_lower else 0
        
        # Try semantic similarity if model available
        try:
            user_embeddings = self.skill_analyzer.compute_skill_embeddings(user_skills)
            job_embeddings = self.skill_analyzer.compute_skill_embeddings(job_skills)
            
            if user_embeddings is not None and job_embeddings is not None:
                # Compute average embedding for each set
                user_avg = np.mean(user_embeddings, axis=0).reshape(1, -1)
                job_avg = np.mean(job_embeddings, axis=0).reshape(1, -1)
                
                # Cosine similarity
                semantic_score = cosine_similarity(user_avg, job_avg)[0][0]
                
                # Combine overlap and semantic scores
                return (overlap_score * 0.6 + semantic_score * 0.4)
        except Exception as e:
            logger.error(f"Semantic similarity error: {e}")
        
        return overlap_score
    
    def _experience_match(self, user_exp: int, job_description: str) -> float:
        """
        Match experience level
        
        Args:
            user_exp: User's years of experience
            job_description: Job description text
            
        Returns:
            Match score between 0 and 1
        """
        desc_lower = job_description.lower()
        
        # Extract experience requirements from description
        if "entry level" in desc_lower or "junior" in desc_lower:
            required_exp = 1
        elif "mid level" in desc_lower or "intermediate" in desc_lower:
            required_exp = 3
        elif "senior" in desc_lower or "lead" in desc_lower:
            required_exp = 5
        elif "principal" in desc_lower or "staff" in desc_lower:
            required_exp = 8
        else:
            # Default to mid-level
            required_exp = 3
        
        # Calculate match
        diff = abs(user_exp - required_exp)
        
        if diff == 0:
            return 1.0
        elif diff <= 1:
            return 0.9
        elif diff <= 2:
            return 0.7
        elif diff <= 3:
            return 0.5
        else:
            return 0.3
    
    def _location_match(self, preferred_locations: List[str], 
                       job_location: str, is_remote: bool) -> float:
        """
        Match location preferences
        
        Args:
            preferred_locations: User's preferred locations
            job_location: Job location
            is_remote: Whether job is remote
            
        Returns:
            Match score between 0 and 1
        """
        # Remote jobs match everyone
        if is_remote:
            return 1.0
        
        if not preferred_locations:
            return 0.7  # Neutral score if no preference
        
        job_location_lower = job_location.lower()
        
        for pref_loc in preferred_locations:
            if pref_loc.lower() in job_location_lower:
                return 1.0
        
        return 0.3  # Low score if location doesn't match
    
    def _salary_match(self, user_min: Optional[float], user_max: Optional[float],
                     job_min: Optional[float], job_max: Optional[float]) -> float:
        """
        Match salary expectations
        
        Args:
            user_min: User's minimum salary expectation
            user_max: User's maximum salary expectation
            job_min: Job's minimum salary
            job_max: Job's maximum salary
            
        Returns:
            Match score between 0 and 1
        """
        # If no salary info, return neutral score
        if not user_min or not job_max:
            return 0.7
        
        # Check if ranges overlap
        if job_max >= user_min:
            # Calculate overlap percentage
            if job_min and user_max:
                overlap_start = max(user_min, job_min)
                overlap_end = min(user_max, job_max)
                
                if overlap_end >= overlap_start:
                    user_range = user_max - user_min
                    overlap = overlap_end - overlap_start
                    return min(1.0, overlap / user_range) if user_range > 0 else 1.0
            
            return 0.8  # Partial match
        
        return 0.2  # Salary too low
    
    def _compare_skills(self, user_skills: List[str], 
                       job_skills: List[str]) -> tuple:
        """
        Compare user skills with job requirements
        
        Returns:
            Tuple of (matching_skills, missing_skills)
        """
        user_skills_lower = {s.lower() for s in user_skills}
        job_skills_lower = {s.lower() for s in job_skills}
        
        matching = []
        missing = []
        
        for job_skill in job_skills:
            if job_skill.lower() in user_skills_lower:
                matching.append(job_skill)
            else:
                missing.append(job_skill)
        
        return matching, missing
    
    def _generate_explanation(self, score: float, matching_skills: List[str],
                            missing_skills: List[str], user_profile: Dict,
                            job: Dict) -> str:
        """
        Generate human-readable explanation for recommendation

        Returns:
            Explanation string
        """
        # Try GPT-powered explanation first
        if self.openai_helper:
            gpt_explanation = self.openai_helper.generate_recommendation_explanation(
                score, matching_skills, missing_skills, user_profile, job
            )
            if gpt_explanation:
                return gpt_explanation

        # Fall back to template-based explanation
        explanations = []
        
        # Skill match explanation
        if matching_skills:
            explanations.append(
                f"You have {len(matching_skills)} matching skills: {', '.join(matching_skills[:3])}"
            )
        
        if missing_skills and len(missing_skills) <= 3:
            explanations.append(
                f"You're missing: {', '.join(missing_skills)}"
            )
        
        # Experience explanation
        user_exp = user_profile.get("experience_years", 0)
        if user_exp >= 5:
            explanations.append("Your senior experience is a great fit")
        elif user_exp >= 2:
            explanations.append("Your experience level matches well")
        
        # Location explanation
        if job.get("remote"):
            explanations.append("Remote position")
        
        # Overall assessment
        if score >= 80:
            prefix = "Excellent match! "
        elif score >= 60:
            prefix = "Good match. "
        else:
            prefix = "Potential match. "
        
        return prefix + ". ".join(explanations)
    
    def _calculate_confidence(self, job: Dict) -> float:
        """
        Calculate confidence level based on data quality
        
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have good data
        if job.get("requirements"):
            confidence += 0.2
        if job.get("description") and len(job["description"]) > 100:
            confidence += 0.15
        if job.get("salary_min") and job.get("salary_max"):
            confidence += 0.15
        
        return min(1.0, confidence)
