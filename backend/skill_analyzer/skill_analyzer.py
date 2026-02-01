"""
Skill Analyzer Module
Extracts, normalizes, and analyzes skills from natural language input
"""

import json
import logging
import re
from typing import List, Dict, Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class SkillAnalyzer:
    """Analyzes and normalizes skills from user input"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Skill Analyzer
        
        Args:
            model_name: Name of the Sentence Transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.skill_taxonomy = self._load_skill_taxonomy()
        self.skill_index = self._build_skill_index()
        
    def _lazy_load_model(self):
        """Lazy load the Sentence Transformer model"""
        if self.model is None and SentenceTransformer is not None:
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def _load_skill_taxonomy(self) -> Dict:
        """Load skill taxonomy from JSON file"""
        taxonomy_path = Path(__file__).parent / "skill_taxonomy.json"
        with open(taxonomy_path, 'r') as f:
            return json.load(f)
    
    def _build_skill_index(self) -> Dict[str, Dict]:
        """Build a searchable index of all skills and synonyms"""
        index = {}
        
        for category, skills in self.skill_taxonomy.items():
            for skill_name, skill_data in skills.items():
                # Add main skill name
                index[skill_name.lower()] = {
                    "name": skill_name,
                    "category": category,
                    "synonyms": skill_data.get("synonyms", []),
                    "related": skill_data.get("related", [])
                }
                
                # Add all synonyms
                for synonym in skill_data.get("synonyms", []):
                    index[synonym.lower()] = {
                        "name": skill_name,
                        "category": category,
                        "synonyms": skill_data.get("synonyms", []),
                        "related": skill_data.get("related", [])
                    }
        
        return index
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from natural language text
        
        Args:
            text: Input text containing skill descriptions
            
        Returns:
            List of extracted skill names (not normalized)
        """
        if not text:
            return []
        
        text_lower = text.lower()
        extracted = []
        
        # Method 1: Direct matching with skill index
        for skill_key in self.skill_index.keys():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill_key) + r'\b'
            if re.search(pattern, text_lower):
                skill_info = self.skill_index[skill_key]
                if skill_info["name"] not in extracted:
                    extracted.append(skill_info["name"])
        
        # Method 2: Extract comma-separated or listed items
        # Common patterns: "Python, JavaScript, React" or "Python and JavaScript"
        separators = [',', ' and ', ' & ', ';', '\n', '|']
        tokens = [text]
        
        for sep in separators:
            new_tokens = []
            for token in tokens:
                new_tokens.extend(token.split(sep))
            tokens = new_tokens
        
        # Clean and check each token
        for token in tokens:
            token = token.strip().lower()
            if token in self.skill_index:
                skill_name = self.skill_index[token]["name"]
                if skill_name not in extracted:
                    extracted.append(skill_name)
        
        return extracted
    
    def normalize_skills(self, skills: List[str]) -> List[Dict]:
        """
        Normalize skills to standard names with categories
        
        Args:
            skills: List of skill names (may include synonyms)
            
        Returns:
            List of normalized skill dictionaries with metadata
        """
        normalized = []
        seen = set()
        
        for skill in skills:
            skill_lower = skill.lower()
            
            if skill_lower in self.skill_index:
                skill_info = self.skill_index[skill_lower]
                skill_name = skill_info["name"]
                
                if skill_name not in seen:
                    normalized.append({
                        "name": skill_name,
                        "category": skill_info["category"],
                        "synonyms": skill_info["synonyms"],
                        "related": skill_info["related"],
                        "proficiency": "intermediate"  # Default proficiency
                    })
                    seen.add(skill_name)
            else:
                # Unknown skill - add as-is with unknown category
                if skill not in seen:
                    normalized.append({
                        "name": skill,
                        "category": "other",
                        "synonyms": [],
                        "related": [],
                        "proficiency": "intermediate"
                    })
                    seen.add(skill)
        
        return normalized
    
    def compute_skill_embeddings(self, skills: List[str]) -> Optional[np.ndarray]:
        """
        Generate embeddings for skill matching using Sentence Transformers
        
        Args:
            skills: List of skill names
            
        Returns:
            Numpy array of embeddings or None if model not available
        """
        model = self._lazy_load_model()
        if model is None or not skills:
            return None
        
        try:
            embeddings = model.encode(skills, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Error computing embeddings: {e}")
            return None
    
    def assign_proficiency(self, skill: str, experience_years: int, 
                          context: str = "") -> str:
        """
        Assign proficiency level based on experience and context
        
        Args:
            skill: Skill name
            experience_years: Years of experience
            context: Additional context from user input
            
        Returns:
            Proficiency level: "beginner", "intermediate", "advanced", "expert"
        """
        # Simple heuristic based on experience
        if experience_years < 1:
            return "beginner"
        elif experience_years < 3:
            return "intermediate"
        elif experience_years < 5:
            return "advanced"
        else:
            return "expert"
    
    def get_skill_category(self, skill: str) -> str:
        """
        Get the category of a skill
        
        Args:
            skill: Skill name
            
        Returns:
            Category name or "other" if not found
        """
        skill_lower = skill.lower()
        if skill_lower in self.skill_index:
            return self.skill_index[skill_lower]["category"]
        return "other"
    
    def get_related_skills(self, skill: str) -> List[str]:
        """
        Get related skills for a given skill
        
        Args:
            skill: Skill name
            
        Returns:
            List of related skill names
        """
        skill_lower = skill.lower()
        if skill_lower in self.skill_index:
            return self.skill_index[skill_lower]["related"]
        return []
    
    def identify_skill_gaps(self, user_skills: List[str], 
                           job_requirements: List[str]) -> List[Dict]:
        """
        Identify missing skills and suggest learning resources
        
        Args:
            user_skills: List of skills the user has
            job_requirements: List of skills required for jobs
            
        Returns:
            List of skill gap dictionaries with learning resources
        """
        # Normalize both lists
        user_skills_normalized = {s.lower() for s in user_skills}
        
        # Find missing skills
        missing_skills = []
        skill_frequency = {}
        
        for req_skill in job_requirements:
            req_skill_lower = req_skill.lower()
            
            # Check if user has this skill or a synonym
            has_skill = False
            if req_skill_lower in user_skills_normalized:
                has_skill = True
            elif req_skill_lower in self.skill_index:
                # Check if user has any synonym
                skill_info = self.skill_index[req_skill_lower]
                for synonym in skill_info["synonyms"]:
                    if synonym.lower() in user_skills_normalized:
                        has_skill = True
                        break
            
            if not has_skill:
                # Track frequency of missing skills
                skill_name = req_skill
                if req_skill_lower in self.skill_index:
                    skill_name = self.skill_index[req_skill_lower]["name"]
                
                if skill_name not in skill_frequency:
                    skill_frequency[skill_name] = 0
                skill_frequency[skill_name] += 1
        
        # Load learning resources
        resources_path = Path(__file__).parent / "learning_resources.json"
        with open(resources_path, 'r') as f:
            learning_resources = json.load(f)
        
        # Build skill gap list with resources
        for skill_name, frequency in sorted(skill_frequency.items(), 
                                           key=lambda x: x[1], reverse=True):
            # Get learning resources for this skill
            resources = learning_resources.get(skill_name, 
                                              learning_resources.get("default", {}))
            
            gap_info = {
                "skill": skill_name,
                "frequency": frequency,
                "impact": self._calculate_impact(frequency, len(job_requirements)),
                "category": self.get_skill_category(skill_name),
                "learning_time": resources.get("estimated_learning_time", "varies"),
                "resources": resources.get("resources", [])
            }
            
            missing_skills.append(gap_info)
        
        return missing_skills
    
    def _calculate_impact(self, frequency: int, total_jobs: int) -> str:
        """
        Calculate the impact of a missing skill
        
        Args:
            frequency: How many jobs require this skill
            total_jobs: Total number of jobs analyzed
            
        Returns:
            Impact level: "high", "medium", "low"
        """
        if total_jobs == 0:
            return "low"
        
        percentage = (frequency / total_jobs) * 100
        
        if percentage >= 50:
            return "high"
        elif percentage >= 25:
            return "medium"
        else:
            return "low"
