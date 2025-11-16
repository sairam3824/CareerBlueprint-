"""
Unit tests for Email Service module
"""

import pytest
from unittest.mock import Mock, patch
from backend.email_service.email_service import EmailService, TemplateEngine, SMTPClient


class TestTemplateEngine:
    """Test suite for TemplateEngine"""
    
    @pytest.fixture
    def engine(self, tmp_path):
        """Create TemplateEngine with temporary directory"""
        return TemplateEngine(templates_dir=str(tmp_path))
    
    def test_render_with_data(self, engine):
        """Test rendering template with data"""
        template = "Hello {{name}}, your score is {{score}}"
        data = {"name": "John", "score": "95"}
        
        # Create template file
        template_path = engine.templates_dir / "test.html"
        with open(template_path, 'w') as f:
            f.write(template)
        
        result = engine.render("test.html", data)
        
        assert "Hello John" in result
        assert "95" in result
    
    def test_render_default_template(self, engine):
        """Test rendering with default template"""
        data = {"user_name": "Test", "job_title": "Engineer"}
        
        result = engine.render("application_confirmation.html", data)
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestEmailService:
    """Test suite for EmailService"""
    
    @pytest.fixture
    def email_service(self):
        """Create EmailService with SMTP"""
        config = {
            "smtp_config": {
                "host": "smtp.test.com",
                "port": 587,
                "username": "test@test.com",
                "password": "password"
            }
        }
        return EmailService(provider="smtp", config=config)
    
    @pytest.fixture
    def sample_application(self):
        """Sample application data"""
        return {
            "user_name": "John Doe",
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco",
            "application_id": "123456",
            "timestamp": "2024-01-01T12:00:00",
            "job_url": "http://example.com/job"
        }
    
    @patch.object(SMTPClient, 'send')
    def test_send_application_confirmation(self, mock_send, email_service, sample_application):
        """Test sending application confirmation"""
        mock_send.return_value = True
        
        result = email_service.send_application_confirmation(
            "user@example.com",
            sample_application
        )
        
        assert result is True
        assert mock_send.called
    
    @patch.object(SMTPClient, 'send')
    def test_send_weekly_digest(self, mock_send, email_service):
        """Test sending weekly digest"""
        mock_send.return_value = True
        
        stats = {"total": 5, "viewed": 10}
        recommendations = [
            {"job": {"title": "Job 1", "company": "Company A"}},
            {"job": {"title": "Job 2", "company": "Company B"}}
        ]
        
        result = email_service.send_weekly_digest(
            "user@example.com",
            stats,
            recommendations
        )
        
        assert result is True
        assert mock_send.called
    
    @patch.object(SMTPClient, 'send')
    def test_retry_send_success_first_try(self, mock_send, email_service):
        """Test retry logic succeeds on first try"""
        mock_send.return_value = True
        
        result = email_service._retry_send(
            "user@example.com",
            "Test Subject",
            "<html>Test</html>"
        )
        
        assert result is True
        assert mock_send.call_count == 1
    
    @patch.object(SMTPClient, 'send')
    def test_retry_send_success_after_retry(self, mock_send, email_service):
        """Test retry logic succeeds after retry"""
        # Fail first, succeed second
        mock_send.side_effect = [False, True]
        
        result = email_service._retry_send(
            "user@example.com",
            "Test Subject",
            "<html>Test</html>",
            max_retries=2
        )
        
        assert result is True
        assert mock_send.call_count == 2
    
    @patch.object(SMTPClient, 'send')
    def test_retry_send_all_fail(self, mock_send, email_service):
        """Test retry logic when all attempts fail"""
        mock_send.return_value = False
        
        result = email_service._retry_send(
            "user@example.com",
            "Test Subject",
            "<html>Test</html>",
            max_retries=2
        )
        
        assert result is False
        assert mock_send.call_count == 3  # Initial + 2 retries
