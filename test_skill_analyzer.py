"""
Quick test script for Skill Analyzer
"""

from backend.skill_analyzer.skill_analyzer import SkillAnalyzer

def test_skill_analyzer():
    print("🚀 Testing Skill Analyzer...\n")
    
    # Initialize analyzer
    analyzer = SkillAnalyzer()
    
    # Test 1: Extract skills from text
    print("Test 1: Extracting skills from text")
    text = "I know Python, JavaScript, React, and I've worked with Docker and AWS"
    extracted = analyzer.extract_skills(text)
    print(f"Input: {text}")
    print(f"Extracted: {extracted}\n")
    
    # Test 2: Normalize skills
    print("Test 2: Normalizing skills")
    skills = ["python", "js", "reactjs", "docker"]
    normalized = analyzer.normalize_skills(skills)
    print(f"Input: {skills}")
    print(f"Normalized:")
    for skill in normalized:
        print(f"  - {skill['name']} ({skill['category']})")
    print()
    
    # Test 3: Identify skill gaps
    print("Test 3: Identifying skill gaps")
    user_skills = ["Python", "JavaScript", "React"]
    job_requirements = ["Python", "JavaScript", "React", "TypeScript", "Docker", 
                       "Kubernetes", "TypeScript", "Docker"]  # TypeScript and Docker appear twice
    gaps = analyzer.identify_skill_gaps(user_skills, job_requirements)
    print(f"User skills: {user_skills}")
    print(f"Job requirements: {set(job_requirements)}")
    print(f"Missing skills:")
    for gap in gaps:
        print(f"  - {gap['skill']} (frequency: {gap['frequency']}, impact: {gap['impact']})")
        print(f"    Learning time: {gap['learning_time']}")
        if gap['resources']:
            print(f"    Resources: {gap['resources'][0]['title']}")
    print()
    
    # Test 4: Get related skills
    print("Test 4: Getting related skills")
    skill = "React"
    related = analyzer.get_related_skills(skill)
    print(f"Skills related to {skill}: {related}\n")
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    test_skill_analyzer()
