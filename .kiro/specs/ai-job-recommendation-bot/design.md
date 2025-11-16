# Design Document

## Overview

The AI Job/Skill Recommendation Bot is built as a modular Python backend with a lightweight frontend chat interface. The system uses Sentence Transformers for semantic skill matching, integrates with multiple job board APIs, tracks applications in Excel/Google Sheets, and sends email confirmations. The architecture emphasizes modularity, allowing easy component replacement and testing.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Chat Interface (React/Vanilla JS)                  │  │
│  │   - User input collection                            │  │
│  │   - Job cards display                                │  │
│  │   - Application history view                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    Fetch API (REST)
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Backend Layer (Python)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   API Server (Flask/aiohttp)                         │  │
│  │   - REST endpoints                                   │  │
│  │   - Request validation                               │  │
│  │   - Error handling                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Core Modules                                       │  │
│  │  ┌────────────────┐  ┌────────────────┐             │  │
│  │  │ Skill Analyzer │  │ Recommendation │             │  │
│  │  │   - NLP        │  │    Engine      │             │  │
│  │  │   - Normalize  │  │   - Matching   │             │  │
│  │  └────────────────┘  └────────────────┘             │  │
│  │  ┌────────────────┐  ┌────────────────┐             │  │
│  │  │  Job Fetcher   │  │   Application  │             │  │
│  │  │   - API calls  │  │    Tracker     │             │  │
│  │  │   - Caching    │  │   - Storage    │             │  │
│  │  └────────────────┘  └────────────────┘             │  │
│  │  ┌────────────────┐                                  │  │
│  │  │ Email Service  │                                  │  │
│  │  │   - Templates  │                                  │  │
│  │  │   - Sending    │                                  │  │
│  │  └────────────────┘                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    External Services
                            │
┌─────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Job Board    │  │ Google       │  │ SendGrid/    │     │
│  │ APIs         │  │ Sheets/Excel │  │ SMTP         │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.9+
- Flask or aiohttp (lightweight async API server)
- Sentence Transformers (all-MiniLM-L6-v2 model)
- Pandas + openpyxl (Excel handling)
- gspread (Google Sheets API)
- requests (HTTP client)
- python-dotenv (configuration)

**Frontend:**
- React (Create React App without Vite) OR Vanilla JavaScript
- HTML5/CSS3
- Fetch API
- Local Storage (session persistence)

**External Services:**
- Adzuna API (primary job source)
- JSearch API via RapidAPI (secondary job source)
- Google Sheets API or local Excel files
- SendGrid or SMTP (email delivery)

## Components and Interfaces

### 1. API Server Module

**Responsibility:** Handle HTTP requests, route to appropriate modules, return responses

**Endpoints:**

```python
POST /api/chat/message
- Input: { "user_id": str, "message": str, "session_id": str }
- Output: { "response": str, "action": str, "data": dict }

POST /api/profile/create
- Input: { "email": str, "skills": list, "experience": int, "preferences": dict }
- Output: { "profile_id": str, "status": str }

GET /api/profile/{email}
- Output: { "profile": dict, "exists": bool }

POST /api/recommendations/generate
- Input: { "profile_id": str, "limit": int }
- Output: { "jobs": list, "match_scores": list }

POST /api/applications/submit
- Input: { "profile_id": str, "job_id": str }
- Output: { "application_id": str, "status": str, "reference": str }

GET /api/applications/history/{email}
- Output: { "applications": list, "stats": dict }

GET /api/health
- Output: { "status": str, "services": dict }
```

**Interface:**
```python
class APIServer:
    def __init__(self, config: Config):
        self.app = Flask(__name__)
        self.skill_analyzer = SkillAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.job_fetcher = JobFetcher()
        self.application_tracker = ApplicationTracker()
        self.email_service = EmailService()
    
    def start(self, host: str, port: int):
        """Start the API server"""
        pass
```

### 2. Skill Analyzer Module

**Responsibility:** Extract, normalize, and categorize skills from user input

**Key Functions:**
- Extract skills from natural language
- Map synonyms to standard terms
- Categorize skills by domain
- Assign proficiency levels

**Interface:**
```python
class SkillAnalyzer:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.skill_taxonomy = self._load_skill_taxonomy()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from natural language text"""
        pass
    
    def normalize_skills(self, skills: List[str]) -> List[Dict]:
        """Normalize skills to standard names with categories"""
        # Returns: [{"name": "Python", "category": "Programming", "synonyms": [...]}]
        pass
    
    def compute_skill_embeddings(self, skills: List[str]) -> np.ndarray:
        """Generate embeddings for skill matching"""
        pass
    
    def identify_skill_gaps(self, user_skills: List[str], 
                           job_requirements: List[str]) -> List[Dict]:
        """Identify missing skills and suggest learning resources"""
        pass
```

**Data:**
- Skill taxonomy JSON (programming languages, frameworks, tools, soft skills)
- Synonym mappings
- Learning resource database

### 3. Recommendation Engine Module

**Responsibility:** Match user profiles with jobs using semantic similarity

**Key Functions:**
- Compute multi-factor match scores
- Rank jobs by relevance
- Explain recommendations

**Interface:**
```python
class RecommendationEngine:
    def __init__(self, skill_analyzer: SkillAnalyzer):
        self.skill_analyzer = skill_analyzer
        self.weights = {
            "skill_match": 0.5,
            "experience_match": 0.2,
            "location_match": 0.15,
            "salary_match": 0.15
        }
    
    def generate_recommendations(self, user_profile: Dict, 
                                jobs: List[Dict], 
                                limit: int = 10) -> List[Dict]:
        """Generate ranked job recommendations"""
        # Returns: [{"job": dict, "score": float, "explanation": str, "matching_skills": list, "missing_skills": list}]
        pass
    
    def compute_match_score(self, user_profile: Dict, job: Dict) -> float:
        """Compute overall match score (0-100)"""
        pass
    
    def _skill_similarity(self, user_skills: List[str], 
                         job_skills: List[str]) -> float:
        """Compute semantic similarity between skill sets"""
        pass
    
    def _experience_match(self, user_exp: int, required_exp: str) -> float:
        """Match experience level"""
        pass
```

### 4. Job Fetcher Module

**Responsibility:** Fetch jobs from multiple APIs, cache results, deduplicate

**Key Functions:**
- Query multiple job board APIs
- Cache responses
- Deduplicate jobs
- Handle API failures gracefully

**Interface:**
```python
class JobFetcher:
    def __init__(self, config: Dict):
        self.adzuna_client = AdzunaClient(config["adzuna_api_key"])
        self.jsearch_client = JSearchClient(config["rapidapi_key"])
        self.cache = JobCache(ttl_hours=6)
    
    def fetch_jobs(self, query: str, location: str = "", 
                   limit: int = 50) -> List[Dict]:
        """Fetch jobs from all sources"""
        pass
    
    def _fetch_from_adzuna(self, query: str, location: str) -> List[Dict]:
        """Fetch from Adzuna API"""
        pass
    
    def _fetch_from_jsearch(self, query: str, location: str) -> List[Dict]:
        """Fetch from JSearch API"""
        pass
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company"""
        pass
    
    def _normalize_job_data(self, job: Dict, source: str) -> Dict:
        """Normalize job data to standard format"""
        pass
```

**Standard Job Format:**
```python
{
    "id": str,
    "title": str,
    "company": str,
    "location": str,
    "remote": bool,
    "description": str,
    "requirements": List[str],
    "salary_min": float,
    "salary_max": float,
    "currency": str,
    "url": str,
    "posted_date": str,
    "source": str
}
```

### 5. Application Tracker Module

**Responsibility:** Store and manage application data in Excel/Google Sheets

**Key Functions:**
- Save applications
- Retrieve application history
- Update application status
- Generate statistics

**Interface:**
```python
class ApplicationTracker:
    def __init__(self, storage_type: str = "excel", config: Dict = None):
        if storage_type == "excel":
            self.storage = ExcelStorage(config["excel_path"])
        else:
            self.storage = GoogleSheetsStorage(config["sheets_id"])
    
    def save_application(self, application: Dict) -> str:
        """Save application and return application ID"""
        pass
    
    def get_user_applications(self, email: str) -> List[Dict]:
        """Retrieve all applications for a user"""
        pass
    
    def update_status(self, application_id: str, status: str):
        """Update application status"""
        pass
    
    def get_statistics(self, email: str) -> Dict:
        """Calculate application statistics"""
        # Returns: {"total": int, "pending": int, "submitted": int, "failed": int}
        pass
```

**Storage Schema:**
```
Columns: application_id, timestamp, user_email, user_name, job_title, 
         company, location, salary, job_url, status, reference_number, 
         skills_matched, retry_count, last_updated
```

### 6. Email Service Module

**Responsibility:** Send confirmation and digest emails

**Key Functions:**
- Send application confirmations
- Send weekly digests
- Render HTML templates
- Handle delivery failures

**Interface:**
```python
class EmailService:
    def __init__(self, provider: str = "sendgrid", config: Dict = None):
        if provider == "sendgrid":
            self.client = SendGridClient(config["sendgrid_api_key"])
        else:
            self.client = SMTPClient(config["smtp_config"])
        self.template_engine = TemplateEngine()
    
    def send_application_confirmation(self, user_email: str, 
                                     application: Dict) -> bool:
        """Send application confirmation email"""
        pass
    
    def send_weekly_digest(self, user_email: str, stats: Dict, 
                          recommendations: List[Dict]) -> bool:
        """Send weekly summary email"""
        pass
    
    def _render_template(self, template_name: str, data: Dict) -> str:
        """Render HTML email template"""
        pass
    
    def _retry_send(self, email_data: Dict, max_retries: int = 2) -> bool:
        """Retry email sending on failure"""
        pass
```

**Email Templates:**
- `application_confirmation.html` - Rich confirmation with job details
- `weekly_digest.html` - Summary with stats and recommendations
- `status_update.html` - Application status changes

### 7. Chat Interface (Frontend)

**Responsibility:** Provide conversational UI for user interaction

**Components:**

```javascript
// Main Chat Component
class ChatInterface {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.messageHistory = [];
    }
    
    async sendMessage(message) {
        // Send to backend and handle response
    }
    
    displayMessage(message, sender) {
        // Render message in chat
    }
    
    displayJobCards(jobs) {
        // Render job recommendations
    }
    
    handleApplyClick(jobId) {
        // Submit application
    }
}

// API Client
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }
    
    async post(endpoint, data) {
        return fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    async get(endpoint) {
        return fetch(`${this.baseURL}${endpoint}`);
    }
}
```

## Data Models

### User Profile
```python
@dataclass
class UserProfile:
    email: str
    name: str
    phone: Optional[str]
    skills: List[str]
    experience_years: int
    preferred_locations: List[str]
    preferred_job_types: List[str]  # ["remote", "hybrid", "onsite"]
    salary_min: Optional[float]
    salary_max: Optional[float]
    currency: str
    created_at: datetime
    updated_at: datetime
```

### Job
```python
@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    remote: bool
    description: str
    requirements: List[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    currency: str
    url: str
    posted_date: datetime
    source: str
```

### Application
```python
@dataclass
class Application:
    id: str
    user_email: str
    job_id: str
    job_title: str
    company: str
    status: str  # ["pending", "submitted", "failed"]
    reference_number: Optional[str]
    submitted_at: datetime
    retry_count: int
    skills_matched: List[str]
```

### Recommendation
```python
@dataclass
class Recommendation:
    job: Job
    match_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    explanation: str
    confidence: float
```

## Error Handling

### Error Types
```python
class BotException(Exception):
    """Base exception for all bot errors"""
    pass

class SkillExtractionError(BotException):
    """Error during skill extraction"""
    pass

class JobFetchError(BotException):
    """Error fetching jobs from API"""
    pass

class ApplicationSubmissionError(BotException):
    """Error submitting application"""
    pass

class StorageError(BotException):
    """Error accessing storage"""
    pass

class EmailDeliveryError(BotException):
    """Error sending email"""
    pass
```

### Error Handling Strategy
- All modules implement try-except blocks with specific exception types
- API endpoints return standardized error responses
- Failed operations are logged with request IDs
- Retry logic for transient failures (API calls, email sending)
- Graceful degradation (e.g., use cached data if API fails)
- User-friendly error messages in chat interface

## Testing Strategy

### Unit Tests
- Test each module independently with mocked dependencies
- Test skill extraction and normalization accuracy
- Test recommendation scoring algorithm
- Test job deduplication logic
- Test storage operations (read/write)

### Integration Tests
- Test API endpoints end-to-end
- Test job fetching from real APIs (with rate limiting)
- Test email sending (to test accounts)
- Test storage with test spreadsheets

### Test Files Structure
```
tests/
├── unit/
│   ├── test_skill_analyzer.py
│   ├── test_recommendation_engine.py
│   ├── test_job_fetcher.py
│   ├── test_application_tracker.py
│   └── test_email_service.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_job_apis.py
│   └── test_end_to_end_flow.py
└── fixtures/
    ├── sample_profiles.json
    ├── sample_jobs.json
    └── skill_taxonomy.json
```

### Testing Tools
- pytest (test framework)
- pytest-mock (mocking)
- pytest-asyncio (async tests)
- responses (HTTP mocking)

## Configuration Management

### Configuration File (config.yaml)
```yaml
server:
  host: "0.0.0.0"
  port: 5000
  debug: false

models:
  sentence_transformer: "all-MiniLM-L6-v2"

apis:
  adzuna:
    app_id: "${ADZUNA_APP_ID}"
    app_key: "${ADZUNA_APP_KEY}"
    base_url: "https://api.adzuna.com/v1/api"
  
  jsearch:
    api_key: "${RAPIDAPI_KEY}"
    base_url: "https://jsearch.p.rapidapi.com"

storage:
  type: "excel"  # or "google_sheets"
  excel_path: "./data/applications.xlsx"
  sheets_id: "${GOOGLE_SHEETS_ID}"

email:
  provider: "sendgrid"  # or "smtp"
  sendgrid_api_key: "${SENDGRID_API_KEY}"
  from_email: "noreply@jobbot.com"
  from_name: "AI Job Bot"

cache:
  ttl_hours: 6
  max_size_mb: 100

logging:
  level: "INFO"
  file: "./logs/bot.log"
```

### Environment Variables
```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
RAPIDAPI_KEY=your_rapidapi_key
SENDGRID_API_KEY=your_sendgrid_key
GOOGLE_SHEETS_ID=your_sheets_id
```

## Deployment

### Docker Setup
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### Requirements.txt
```
flask==2.3.0
sentence-transformers==2.2.2
pandas==2.0.0
openpyxl==3.1.0
gspread==5.9.0
requests==2.31.0
python-dotenv==1.0.0
sendgrid==6.10.0
pytest==7.3.0
pytest-mock==3.10.0
```

### Deployment Steps
1. Build Docker image
2. Set environment variables
3. Deploy to cloud platform (Render, Railway, Heroku)
4. Configure domain and SSL
5. Set up monitoring and logging

## Performance Considerations

- **Caching:** Cache job listings for 6 hours to reduce API calls
- **Async Operations:** Use async/await for concurrent API calls
- **Batch Processing:** Process multiple jobs in parallel during recommendation
- **Model Loading:** Load Sentence Transformer model once at startup
- **Connection Pooling:** Reuse HTTP connections for API calls
- **Lazy Loading:** Load frontend components on demand
- **Compression:** Compress API responses with gzip

## Security Considerations

- Store API keys in environment variables, never in code
- Validate all user inputs before processing
- Sanitize data before storing in spreadsheets
- Use HTTPS for all API communication
- Implement rate limiting to prevent abuse
- Hash sensitive user data
- Implement CORS properly for frontend-backend communication
- Regular dependency updates for security patches
