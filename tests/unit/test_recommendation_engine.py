"""
Unit tests for Recommendation Engine module
"""

import pytest
from unittest.mock import Mock
from backend.recommendation_engine.recommendation_engine import RecommendationEngine
from backend.skill_analyzer.skill_analyzer import SkillAnalyzer


class TestRecommendationEngine:
    """Test suite for RecommendationEngine"""
    
    @pytest.fixture
    def skill_analyzer(self):
        """Create mock SkillAnalyzer"""
        return SkillAnalyzer()
    
    @pytest.fixture
    def engine(self, skill_analyzer):
        """Create RecommendationEngine instance"""
        return RecommendationEngine(skill_analyzer)
    
    @pytest.fixture
    def sample_user_profile(self):
        """Sample user profile for testing"""
        return {
            "skills": ["Python", "JavaScript", "React"],
            "experience_years": 3,
            "preferred_locations": ["San Francisco"],
            "salary_min": 80000,
            "salary_max": 120000
        }
    
    @pytest.fixture
    def sample_jobs(self):
        """Sample jobs for testing"""
        return [
            {
                "id": "1",
                "title": "Python Developer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "remote": False,
                "description": "Mid-level Python developer needed",
                "requirements": ["Python", "JavaScript", "Docker"],
                "salary_min": 90000,
                "salary_max": 110000
            },
            {
                "id": "2",
                "title": "Senior React Engineer",
                "company": "StartupCo",
                "location": "Remote",
                "remote": True,
                "description": "Senior React developer",
                "requirements": ["React", "TypeScript", "Node.js"],
                "salary_min": 120000,
                "salary_max": 150000
            }
        ]
    
    def test_generate_recommendations(self, engine, sample_user_profile, sample_jobs):
        """Test generating recommendations"""
        recommendations = engine.generate_recommendations(
            sample_user_profile, sample_jobs, limit=10
        )
        
        assert len(recommendations) <= 10
        assert len(recommendations) == len(sample_jobs)
        
        # Check structure
        for rec in recommendations:
            assert "job" in rec
            assert "match_score" in rec
            assert "matching_skills" in rec
            assert "missing_skills" in rec
            assert "explanation" in rec
            assert "confidence" in rec
    
    def test_recommendations_are_sorted(self, engine, sample_user_profile, sample_jobs):
        """Test that recommendations are sorted by score"""
        recommendations = engine.generate_recommendations(
            sample_user_profile, sample_jobs, limit=10
        )
        
        # Scores should be in descending order
        scores = [r["match_score"] for r in recommendations]
        assert scores == sorted(scores, reverse=True)
    
    def test_compute_match_score(self, engine, sample_user_profile, sample_jobs):
        """Test match score computation"""
        score = engine.compute_match_score(sample_user_profile, sample_jobs[0])
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_skill_similarity(self, engine):
        """Test skill similarity calculation"""
        user_skills = ["Python", "JavaScript", "React"]
        job_skills = ["Python", "JavaScript", "Docker"]
        
        similarity = engine._skill_similarity(user_skills, job_skills)
        
        assert 0 <= similarity <= 1
        # Should have some similarity (2 out of 3 skills match)
        assert similarity > 0
    
    def test_skill_similarity_no_match(self, engine):
        """Test skill similarity with no matching skills"""
        user_skills = ["Python", "JavaScript"]
        job_skills = ["Java", "C++"]
        
        similarity = engine._skill_similarity(user_skills, job_skills)
        
        assert similarity == 0
    
    def test_skill_similarity_perfect_match(self, engine):
        """Test skill similarity with perfect match"""
        skills = ["Python", "JavaScript", "React"]
        
        similarity = engine._skill_similarity(skills, skills)
        
        assert similarity > 0.9  # Should be very high
    
    def test_experience_match(self, engine):
        """Test experience matching"""
        # Mid-level position
        score = engine._experience_match(3, "mid level developer position")
        assert score > 0.7
        
        # Entry level
        score = engine._experience_match(1, "entry level junior developer")
        assert score > 0.7
        
        # Senior level
        score = engine._experience_match(6, "senior lead developer")
        assert score > 0.7
    
    def test_location_match_remote(self, engine):
        """Test location matching for remote jobs"""
        score = engine._location_match(["San Francisco"], "New York", True)
        
        # Remote jobs should match everyone
        assert score == 1.0
    
    def test_location_match_preferred(self, engine):
        """Test location matching with preferred location"""
        score = engine._location_match(
            ["San Francisco"], 
            "San Francisco, CA", 
            False
        )
        
        assert score == 1.0
    
    def test_location_match_no_preference(self, engine):
        """Test location matching with no preference"""
        score = engine._location_match([], "New York", False)
        
        # Should return neutral score
        assert score == 0.7
    
    def test_salary_match_in_range(self, engine):
        """Test salary matching when in range"""
        score = engine._salary_match(80000, 120000, 90000, 110000)
        
        # Should have good match
        assert score > 0.7
    
    def test_salary_match_too_low(self, engine):
        """Test salary matching when salary is too low"""
        score = engine._salary_match(100000, 150000, 50000, 80000)
        
        # Should have low match
        assert score < 0.5
    
    def test_salary_match_no_info(self, engine):
        """Test salary matching with no salary info"""
        score = engine._salary_match(None, None, None, None)
        
        # Should return neutral score
        assert score == 0.7
    
    def test_compare_skills(self, engine):
        """Test skill comparison"""
        user_skills = ["Python", "JavaScript", "React"]
        job_skills = ["Python", "JavaScript", "Docker", "Kubernetes"]
        
        matching, missing = engine._compare_skills(user_skills, job_skills)
        
        assert "Python" in matching
        assert "JavaScript" in matching
        assert "Docker" in missing
        assert "Kubernetes" in missing
    
    def test_generate_explanation(self, engine, sample_user_profile, sample_jobs):
        """Test explanation generation"""
        score = 85.0
        matching_skills = ["Python", "JavaScript"]
        missing_skills = ["Docker"]
        
        explanation = engine._generate_explanation(
            score, matching_skills, missing_skills, 
            sample_user_profile, sample_jobs[0]
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        # Should mention matching skills
        assert "Python" in explanation or "JavaScript" in explanation
    
    def test_calculate_confidence(self, engine, sample_jobs):
        """Test confidence calculation"""
        confidence = engine._calculate_confidence(sample_jobs[0])
        
        assert 0 <= confidence <= 1
        
        # Job with more data should have higher confidence
        complete_job = {
            "requirements": ["Python", "JavaScript"],
            "description": "A" * 200,  # Long description
            "salary_min": 80000,
            "salary_max": 120000
        }
        
        incomplete_job = {
            "requirements": [],
            "description": "Short",
            "salary_min": None,
            "salary_max": None
        }
        
        conf_complete = engine._calculate_confidence(complete_job)
        conf_incomplete = engine._calculate_confidence(incomplete_job)
        
        assert conf_complete > conf_incomplete
    
    def test_empty_jobs_list(self, engine, sample_user_profile):
        """Test with empty jobs list"""
        recommendations = engine.generate_recommendations(
            sample_user_profile, [], limit=10
        )
        
        assert recommendations == []
    
    def test_limit_recommendations(self, engine, sample_user_profile):
        """Test that limit is respected"""
        # Create many jobs
        many_jobs = [
            {
                "id": str(i),
                "title": f"Job {i}",
                "company": "Company",
                "location": "Location",
                "remote": False,
                "description": "Description",
                "requirements": ["Python"],
                "salary_min": 80000,
                "salary_max": 120000
            }
            for i in range(20)
        ]
        
        recommendations = engine.generate_recommendations(
            sample_user_profile, many_jobs, limit=5
        )
        
        assert len(recommendations) == 5
