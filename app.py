"""
AI Job Recommendation Bot - Main Application
Flask API Server
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yaml
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Import modules
from backend.skill_analyzer.skill_analyzer import SkillAnalyzer
from backend.recommendation_engine.recommendation_engine import RecommendationEngine
from backend.job_fetcher.job_fetcher import JobFetcher
from backend.application_tracker.application_tracker import ApplicationTracker
from backend.email_service.email_service import EmailService

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load configuration from config.yaml and environment variables"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables
    config['apis']['adzuna']['app_id'] = os.getenv('ADZUNA_APP_ID', '')
    config['apis']['adzuna']['app_key'] = os.getenv('ADZUNA_APP_KEY', '')
    config['apis']['jsearch']['api_key'] = os.getenv('RAPIDAPI_KEY', '')
    config['email']['sendgrid_api_key'] = os.getenv('SENDGRID_API_KEY', '')
    
    return config

config = load_config()

# Initialize modules
logger.info("Initializing modules...")
skill_analyzer = SkillAnalyzer(config['models']['sentence_transformer'])
recommendation_engine = RecommendationEngine(skill_analyzer)

job_fetcher_config = {
    "adzuna_app_id": config['apis']['adzuna']['app_id'],
    "adzuna_app_key": config['apis']['adzuna']['app_key'],
    "rapidapi_key": config['apis']['jsearch']['api_key'],
    "cache_ttl_hours": config['cache']['ttl_hours']
}
job_fetcher = JobFetcher(job_fetcher_config)

application_tracker = ApplicationTracker(
    storage_type=config['storage']['type'],
    config=config['storage']
)

email_service = EmailService(
    provider=config['email']['provider'],
    config=config['email']
)

logger.info("All modules initialized successfully")

# In-memory session storage (for demo - use Redis in production)
sessions = {}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "skill_analyzer": "ok",
            "job_fetcher": "ok",
            "recommendation_engine": "ok",
            "application_tracker": "ok",
            "email_service": "ok"
        }
    })


@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """Handle chat messages and extract skills"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        logger.info(f"Chat message received: {message[:50]}...")
        
        # Extract skills from message
        extracted_skills = skill_analyzer.extract_skills(message)
        
        # Normalize skills
        normalized_skills = skill_analyzer.normalize_skills(extracted_skills)
        
        # Store in session
        if session_id not in sessions:
            sessions[session_id] = {}
        
        sessions[session_id]['skills'] = [s['name'] for s in normalized_skills]
        sessions[session_id]['last_message'] = message
        
        response = {
            "response": f"Great! I found these skills: {', '.join([s['name'] for s in normalized_skills])}",
            "action": "skills_extracted",
            "data": {
                "skills": normalized_skills,
                "extracted_count": len(normalized_skills)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile/create', methods=['POST'])
def create_profile():
    """Create user profile"""
    try:
        data = request.json
        
        profile = {
            "email": data.get('email'),
            "name": data.get('name', ''),
            "skills": data.get('skills', []),
            "experience_years": data.get('experience', 0),
            "preferred_locations": data.get('locations', []),
            "preferred_job_types": data.get('job_types', []),
            "salary_min": data.get('salary_min'),
            "salary_max": data.get('salary_max'),
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Profile created for {profile['email']}")
        
        return jsonify({
            "profile_id": profile['email'],
            "status": "created"
        })
        
    except Exception as e:
        logger.error(f"Profile creation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile/<email>', methods=['GET'])
def get_profile(email):
    """Get user profile"""
    try:
        # In a real app, fetch from database
        return jsonify({
            "profile": {},
            "exists": False
        })
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/recommendations/generate', methods=['POST'])
def generate_recommendations():
    """Generate job recommendations"""
    try:
        data = request.json
        user_profile = data.get('profile', {})
        limit = data.get('limit', 10)
        
        logger.info(f"Generating recommendations for skills: {user_profile.get('skills', [])}")
        
        # Build search query from skills
        skills = user_profile.get('skills', [])
        if not skills:
            return jsonify({"error": "No skills provided"}), 400
        
        query = " ".join(skills[:3])  # Use top 3 skills for search
        
        # Fetch jobs
        jobs = job_fetcher.fetch_jobs(
            query=query,
            location=user_profile.get('preferred_locations', [''])[0] if user_profile.get('preferred_locations') else '',
            limit=50
        )
        
        logger.info(f"Fetched {len(jobs)} jobs")
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(
            user_profile, jobs, limit
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        # Identify skill gaps
        all_job_requirements = []
        for job in jobs[:10]:  # Analyze top 10 jobs
            all_job_requirements.extend(job.get('requirements', []))
        
        skill_gaps = skill_analyzer.identify_skill_gaps(
            user_profile.get('skills', []),
            all_job_requirements
        )
        
        return jsonify({
            "recommendations": recommendations,
            "skill_gaps": skill_gaps[:5],  # Top 5 gaps
            "total_jobs_analyzed": len(jobs)
        })
        
    except Exception as e:
        logger.error(f"Recommendation generation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/applications/submit', methods=['POST'])
def submit_application():
    """Submit job application"""
    try:
        data = request.json
        
        application = {
            "user_email": data.get('user_email'),
            "user_name": data.get('user_name', ''),
            "job_title": data.get('job_title'),
            "company": data.get('company'),
            "location": data.get('location', ''),
            "salary": data.get('salary', ''),
            "job_url": data.get('job_url', ''),
            "skills_matched": data.get('skills_matched', []),
            "status": "submitted"
        }
        
        # Save application
        app_id = application_tracker.save_application(application)
        
        logger.info(f"Application submitted: {app_id}")
        
        # Send confirmation email
        try:
            email_service.send_application_confirmation(
                application['user_email'],
                {**application, 'application_id': app_id, 'timestamp': datetime.now().isoformat()}
            )
        except Exception as e:
            logger.error(f"Email send failed: {e}")
        
        return jsonify({
            "application_id": app_id,
            "status": "submitted",
            "reference": app_id[:8]
        })
        
    except Exception as e:
        logger.error(f"Application submission error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/applications/history/<email>', methods=['GET'])
def get_application_history(email):
    """Get application history for user"""
    try:
        applications = application_tracker.get_user_applications(email)
        stats = application_tracker.get_statistics(email)
        
        return jsonify({
            "applications": applications,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Application history error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    host = config['server']['host']
    port = config['server']['port']
    debug = config['server']['debug']
    
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
