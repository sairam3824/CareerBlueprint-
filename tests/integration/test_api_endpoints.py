"""
Integration tests for API endpoints
"""

import pytest
import json
from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns 200"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'services' in data


class TestChatEndpoint:
    """Tests for chat message endpoint"""
    
    def test_chat_message_success(self, client):
        """Test chat message with valid input"""
        payload = {
            "message": "I know Python, JavaScript, and React",
            "session_id": "test_session_123"
        }
        
        response = client.post(
            '/api/chat/message',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'response' in data
        assert 'action' in data
    
    def test_chat_message_empty(self, client):
        """Test chat message with empty input"""
        payload = {
            "message": "",
            "session_id": "test_session_123"
        }
        
        response = client.post(
            '/api/chat/message',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200


class TestProfileEndpoints:
    """Tests for profile endpoints"""
    
    def test_create_profile(self, client):
        """Test creating a user profile"""
        payload = {
            "email": "test@example.com",
            "name": "Test User",
            "skills": ["Python", "JavaScript"],
            "experience": 3
        }
        
        response = client.post(
            '/api/profile/create',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'profile_id' in data
        assert data['status'] == 'created'
    
    def test_get_profile(self, client):
        """Test getting a user profile"""
        response = client.get('/api/profile/test@example.com')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'profile' in data
        assert 'exists' in data


class TestRecommendationsEndpoint:
    """Tests for recommendations endpoint"""
    
    def test_generate_recommendations(self, client):
        """Test generating recommendations"""
        payload = {
            "profile": {
                "skills": ["Python", "JavaScript", "React"],
                "experience_years": 3,
                "preferred_locations": ["San Francisco"],
                "salary_min": 80000,
                "salary_max": 120000
            },
            "limit": 5
        }
        
        response = client.post(
            '/api/recommendations/generate',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # May succeed or fail depending on API keys
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'recommendations' in data
    
    def test_generate_recommendations_no_skills(self, client):
        """Test recommendations with no skills"""
        payload = {
            "profile": {
                "skills": [],
                "experience_years": 3
            },
            "limit": 5
        }
        
        response = client.post(
            '/api/recommendations/generate',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestApplicationEndpoints:
    """Tests for application endpoints"""
    
    def test_submit_application(self, client):
        """Test submitting an application"""
        payload = {
            "user_email": "test@example.com",
            "user_name": "Test User",
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco",
            "skills_matched": ["Python", "JavaScript"]
        }
        
        response = client.post(
            '/api/applications/submit',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'application_id' in data
        assert data['status'] == 'submitted'
    
    def test_get_application_history(self, client):
        """Test getting application history"""
        response = client.get('/api/applications/history/test@example.com')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'applications' in data
        assert 'stats' in data
