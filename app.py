"""
AI Job Recommendation Bot - Main Application
Flask API Server
"""

import re
import os
import json
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import yaml
from dotenv import load_dotenv
import logging
from datetime import datetime

# Import modules
from backend.skill_analyzer.skill_analyzer import SkillAnalyzer
from backend.recommendation_engine.recommendation_engine import RecommendationEngine
from backend.job_fetcher.job_fetcher import JobFetcher
from backend.application_tracker.application_tracker import ApplicationTracker
from backend.email_service.email_service import EmailService
from backend.openai_helper.openai_helper import OpenAIHelper

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# CORS: driven by CORS_ORIGINS env var; empty/unset = same-origin only
_cors_origins = os.getenv('CORS_ORIGINS', '').strip()
if _cors_origins:
    CORS(app, origins=[o.strip() for o in _cors_origins.split(',') if o.strip()])
else:
    CORS(app, origins=[])

# Ensure required directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

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


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_config():
    """Load configuration from config.yaml and environment variables"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Replace environment variables
    config['apis']['adzuna']['app_id'] = os.getenv('ADZUNA_APP_ID', '')
    config['apis']['adzuna']['app_key'] = os.getenv('ADZUNA_APP_KEY', '')
    config['apis']['jsearch']['api_key'] = os.getenv('RAPIDAPI_KEY', '')
    config['email']['sendgrid_api_key'] = os.getenv('SENDGRID_API_KEY', '')
    config['apis']['openai']['api_key'] = os.getenv('OPENAI_API_KEY', '')

    return config


def validate_config(config):
    """Warn at startup about missing API keys / configuration."""
    adzuna_ok = bool(config['apis']['adzuna'].get('app_id')) and bool(config['apis']['adzuna'].get('app_key'))
    jsearch_ok = bool(config['apis']['jsearch'].get('api_key'))
    sendgrid_ok = bool(config['email'].get('sendgrid_api_key'))

    if not adzuna_ok:
        logger.warning("Adzuna API credentials are missing – Adzuna job search will not work")
    if not jsearch_ok:
        logger.warning("JSearch (RapidAPI) key is missing – JSearch job search will not work")
    if not sendgrid_ok:
        logger.warning("SendGrid API key is missing – email notifications will not work")
    if not adzuna_ok and not jsearch_ok:
        logger.warning("No job API keys configured at all – job fetching will be unavailable")

    openai_ok = bool(config['apis']['openai'].get('api_key'))
    if not openai_ok:
        logger.info("OpenAI API key is missing – GPT features will be disabled")


config = load_config()
validate_config(config)

# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["30 per minute"],
    storage_uri="memory://",
)

# ---------------------------------------------------------------------------
# SQLite profile helpers
# ---------------------------------------------------------------------------

DB_PATH = os.path.join('data', 'jobbot.db')


def _get_db():
    """Return a new SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_profiles_table():
    """Create the profiles table if it doesn't exist."""
    conn = _get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                email TEXT PRIMARY KEY,
                name TEXT,
                skills TEXT,
                experience_years INTEGER,
                preferred_locations TEXT,
                preferred_job_types TEXT,
                salary_min REAL,
                salary_max REAL,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _save_profile(profile: dict):
    """Insert or replace a profile."""
    conn = _get_db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO profiles
               (email, name, skills, experience_years, preferred_locations,
                preferred_job_types, salary_min, salary_max, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profile['email'],
                profile.get('name', ''),
                json.dumps(profile.get('skills', [])),
                profile.get('experience_years', 0),
                json.dumps(profile.get('preferred_locations', [])),
                json.dumps(profile.get('preferred_job_types', [])),
                profile.get('salary_min'),
                profile.get('salary_max'),
                profile.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _load_profile(email: str) -> dict | None:
    """Load a profile by email, or return None."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT * FROM profiles WHERE email = ?", (email,)
        ).fetchone()
        if row is None:
            return None
        profile = dict(row)
        # Deserialise JSON columns
        for col in ('skills', 'preferred_locations', 'preferred_job_types'):
            val = profile.get(col)
            if isinstance(val, str):
                try:
                    profile[col] = json.loads(val)
                except json.JSONDecodeError:
                    profile[col] = []
        return profile
    finally:
        conn.close()


_init_profiles_table()

# ---------------------------------------------------------------------------
# Initialize modules
# ---------------------------------------------------------------------------

logger.info("Initializing modules...")
skill_analyzer = SkillAnalyzer(config['models']['sentence_transformer'])

openai_config = config['apis']['openai']
openai_helper = OpenAIHelper(
    api_key=openai_config.get('api_key', ''),
    model=openai_config.get('model', 'gpt-4o-mini'),
    max_tokens=openai_config.get('max_tokens', 512),
    temperature=openai_config.get('temperature', 0.7),
)

recommendation_engine = RecommendationEngine(skill_analyzer, openai_helper)

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

# Transient chat state (not persisted — only holds in-flight chat context)
chat_sessions = {}

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _validate_email(email: str) -> str | None:
    """Return an error string if email is invalid, else None."""
    if not email:
        return "Email is required"
    if len(email) > 254:
        return "Email must be at most 254 characters"
    if not EMAIL_RE.match(email):
        return "A valid email address is required"
    return None


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(429)
def ratelimit_exceeded(_e):
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429


@app.errorhandler(500)
def internal_error(_e):
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def serve_frontend():
    """Serve the frontend index.html"""
    return send_from_directory('frontend', 'index.html')


@app.route('/frontend/<path:filename>')
def serve_static(filename):
    """Serve static files from the frontend directory"""
    return send_from_directory('frontend', filename)


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
            "email_service": "ok",
            "openai": "ok" if openai_helper.available else "disabled"
        }
    })


@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """Handle chat messages and extract skills"""
    try:
        data = request.json
        if not data or not data.get('message', '').strip():
            return jsonify({"error": "Message must not be empty"}), 400

        message = data.get('message', '')
        session_id = data.get('session_id', '')

        logger.info(f"Chat message received: {message[:50]}...")

        # Extract skills from message (regex-based, fast and free)
        extracted_skills = skill_analyzer.extract_skills(message)

        # Try GPT-based skill extraction and merge results
        gpt_skills = openai_helper.extract_skills_gpt(
            message,
            known_skills=list(skill_analyzer.skill_index.keys()),
        )
        if gpt_skills:
            existing_lower = {s.lower() for s in extracted_skills}
            for skill in gpt_skills:
                if skill.lower() not in existing_lower:
                    extracted_skills.append(skill)
                    existing_lower.add(skill.lower())

        # Normalize skills
        normalized_skills = skill_analyzer.normalize_skills(extracted_skills)

        # Store in transient chat session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {}

        skill_names = [s['name'] for s in normalized_skills]
        chat_sessions[session_id]['skills'] = skill_names
        chat_sessions[session_id]['last_message'] = message

        # Try GPT chat response, fall back to template
        template_response = f"Great! I found these skills: {', '.join(skill_names)}"
        gpt_response = openai_helper.generate_chat_response(
            message,
            skill_names,
            session_context=chat_sessions.get(session_id),
        )

        response = {
            "response": gpt_response or template_response,
            "action": "skills_extracted",
            "data": {
                "skills": normalized_skills,
                "extracted_count": len(normalized_skills)
            }
        }

        return jsonify(response)

    except Exception as e:
        logger.error("Chat message error", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@app.route('/api/profile/create', methods=['POST'])
def create_profile():
    """Create user profile"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        email = data.get('email', '')
        email_err = _validate_email(email)
        if email_err:
            return jsonify({"error": email_err}), 400

        profile = {
            "email": email,
            "name": data.get('name', ''),
            "skills": data.get('skills', []),
            "experience_years": data.get('experience', 0),
            "preferred_locations": data.get('locations', []),
            "preferred_job_types": data.get('job_types', []),
            "salary_min": data.get('salary_min'),
            "salary_max": data.get('salary_max'),
            "created_at": datetime.now().isoformat()
        }

        _save_profile(profile)

        logger.info(f"Profile created for {profile['email']}")

        return jsonify({
            "profile_id": profile['email'],
            "status": "created",
            "profile": profile
        })

    except Exception as e:
        logger.error("Profile creation error", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@app.route('/api/profile/<email>', methods=['GET'])
def get_profile_endpoint(email):
    """Get user profile"""
    try:
        email_err = _validate_email(email)
        if email_err:
            return jsonify({"error": email_err}), 400

        profile = _load_profile(email)
        if profile:
            return jsonify({
                "profile": profile,
                "exists": True
            })
        return jsonify({
            "profile": {},
            "exists": False
        })
    except Exception as e:
        logger.error("Profile fetch error", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@app.route('/api/recommendations/generate', methods=['POST'])
@limiter.limit("10 per minute")
def generate_recommendations():
    """Generate job recommendations"""
    try:
        data = request.json
        if not data or not data.get('profile'):
            return jsonify({"error": "Profile is required"}), 400

        user_profile = data.get('profile', {})
        limit = data.get('limit', 10)

        logger.info(f"Generating recommendations for skills: {user_profile.get('skills', [])}")

        # Build search query from skills
        skills = user_profile.get('skills', [])
        if not skills or not isinstance(skills, list):
            return jsonify({"error": "A non-empty skills list is required in the profile"}), 400

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
        logger.error("Recommendation generation error", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@app.route('/api/applications/submit', methods=['POST'])
@limiter.limit("10 per minute")
def submit_application():
    """Submit job application"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # --- input validation ---
        errors = []

        user_email = (data.get('user_email') or '').strip()
        email_err = _validate_email(user_email)
        if email_err:
            errors.append(email_err)

        job_title = (data.get('job_title') or '').strip()
        if not job_title:
            errors.append("job_title is required")
        elif len(job_title) > 200:
            errors.append("job_title must be at most 200 characters")

        company = (data.get('company') or '').strip()
        if not company:
            errors.append("company is required")
        elif len(company) > 200:
            errors.append("company must be at most 200 characters")

        # Optional field length limits
        for field, max_len in [('location', 200), ('salary', 100), ('job_url', 2000), ('user_name', 200)]:
            val = data.get(field)
            if val and len(str(val)) > max_len:
                errors.append(f"{field} must be at most {max_len} characters")

        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        application = {
            "user_email": user_email,
            "user_name": data.get('user_name', ''),
            "job_title": job_title,
            "company": company,
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
        logger.error("Application submission error", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@app.route('/api/applications/history/<email>', methods=['GET'])
def get_application_history(email):
    """Get application history for user"""
    try:
        email_err = _validate_email(email)
        if email_err:
            return jsonify({"error": email_err}), 400

        applications = application_tracker.get_user_applications(email)
        stats = application_tracker.get_statistics(email)

        return jsonify({
            "applications": applications,
            "stats": stats
        })

    except Exception as e:
        logger.error("Application history error", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


if __name__ == '__main__':
    host = config['server']['host']
    port = config['server']['port']
    debug = os.getenv('FLASK_DEBUG', str(config['server'].get('debug', False))).lower() in ('true', '1', 'yes')

    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
