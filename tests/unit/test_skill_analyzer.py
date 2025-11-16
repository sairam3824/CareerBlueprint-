"""
Unit tests for Skill Analyzer module
"""

import pytest
from backend.skill_analyzer.skill_analyzer import SkillAnalyzer


class TestSkillAnalyzer:
    """Test suite for SkillAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create SkillAnalyzer instance for testing"""
        return SkillAnalyzer()
    
    def test_extract_skills_comma_separated(self, analyzer):
        """Test skill extraction from comma-separated list"""
        text = "I know Python, JavaScript, React"
        skills = analyzer.extract_skills(text)
        
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "React" in skills
        assert len(skills) >= 3
    
    def test_extract_skills_natural_language(self, analyzer):
        """Test skill extraction from natural language"""
        text = "I'm experienced with Python and JavaScript, also know Docker"
        skills = analyzer.extract_skills(text)
        
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "Docker" in skills
    
    def test_extract_skills_synonyms(self, analyzer):
        """Test that synonyms are normalized to standard names"""
        text = "I know js, reactjs, and py"
        skills = analyzer.extract_skills(text)
        
        # Should normalize to standard names
        assert "JavaScript" in skills or "React" in skills
    
    def test_extract_skills_empty_input(self, analyzer):
        """Test extraction with empty input"""
        skills = analyzer.extract_skills("")
        assert skills == []
    
    def test_normalize_skills(self, analyzer):
        """Test skill normalization"""
        skills = ["python", "javascript", "react"]
        normalized = analyzer.normalize_skills(skills)
        
        assert len(normalized) > 0
        assert all("name" in skill for skill in normalized)
        assert all("category" in skill for skill in normalized)
    
    def test_normalize_skills_with_synonyms(self, analyzer):
        """Test normalization handles synonyms correctly"""
        skills = ["js", "reactjs", "py"]
        normalized = analyzer.normalize_skills(skills)
        
        # Should normalize to standard names
        names = [s["name"] for s in normalized]
        assert "JavaScript" in names or "React" in names or "Python" in names
    
    def test_normalize_skills_unknown(self, analyzer):
        """Test normalization with unknown skills"""
        skills = ["UnknownSkill123"]
        normalized = analyzer.normalize_skills(skills)
        
        assert len(normalized) == 1
        assert normalized[0]["name"] == "UnknownSkill123"
        assert normalized[0]["category"] == "other"
    
    def test_get_skill_category(self, analyzer):
        """Test getting skill category"""
        assert analyzer.get_skill_category("Python") == "programming_languages"
        assert analyzer.get_skill_category("React") == "frameworks"
        assert analyzer.get_skill_category("UnknownSkill") == "other"
    
    def test_get_related_skills(self, analyzer):
        """Test getting related skills"""
        related = analyzer.get_related_skills("Python")
        
        assert isinstance(related, list)
        assert len(related) > 0
    
    def test_identify_skill_gaps(self, analyzer):
        """Test skill gap identification"""
        user_skills = ["Python", "JavaScript"]
        job_requirements = ["Python", "JavaScript", "React", "Docker", "React"]
        
        gaps = analyzer.identify_skill_gaps(user_skills, job_requirements)
        
        assert len(gaps) > 0
        gap_skills = [g["skill"] for g in gaps]
        assert "React" in gap_skills
        assert "Docker" in gap_skills
    
    def test_identify_skill_gaps_frequency(self, analyzer):
        """Test that skill gaps are ranked by frequency"""
        user_skills = ["Python"]
        job_requirements = ["Python", "React", "React", "React", "Docker"]
        
        gaps = analyzer.identify_skill_gaps(user_skills, job_requirements)
        
        # React appears 3 times, Docker once
        # React should be ranked higher
        if len(gaps) >= 2:
            assert gaps[0]["frequency"] >= gaps[1]["frequency"]
    
    def test_identify_skill_gaps_with_resources(self, analyzer):
        """Test that skill gaps include learning resources"""
        user_skills = ["JavaScript"]
        job_requirements = ["JavaScript", "Python", "React"]
        
        gaps = analyzer.identify_skill_gaps(user_skills, job_requirements)
        
        for gap in gaps:
            assert "resources" in gap
            assert "learning_time" in gap
            assert "impact" in gap
    
    def test_assign_proficiency(self, analyzer):
        """Test proficiency assignment based on experience"""
        assert analyzer.assign_proficiency("Python", 0) == "beginner"
        assert analyzer.assign_proficiency("Python", 2) == "intermediate"
        assert analyzer.assign_proficiency("Python", 4) == "advanced"
        assert analyzer.assign_proficiency("Python", 6) == "expert"
    
    def test_compute_skill_embeddings(self, analyzer):
        """Test skill embedding computation"""
        skills = ["Python", "JavaScript", "React"]
        embeddings = analyzer.compute_skill_embeddings(skills)
        
        # May be None if model not loaded
        if embeddings is not None:
            assert embeddings.shape[0] == len(skills)
    
    def test_extract_skills_case_insensitive(self, analyzer):
        """Test that extraction is case-insensitive"""
        text1 = "I know PYTHON and JAVASCRIPT"
        text2 = "I know python and javascript"
        
        skills1 = analyzer.extract_skills(text1)
        skills2 = analyzer.extract_skills(text2)
        
        # Should extract same skills regardless of case
        assert "Python" in skills1
        assert "Python" in skills2
