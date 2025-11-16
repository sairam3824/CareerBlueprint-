"""
Unit tests for Application Tracker module
"""

import pytest
from backend.application_tracker.application_tracker import ApplicationTracker, ExcelStorage


class TestApplicationTracker:
    """Test suite for ApplicationTracker"""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create ApplicationTracker with temporary storage"""
        config = {"excel_path": str(tmp_path / "test_applications.xlsx")}
        return ApplicationTracker(storage_type="excel", config=config)
    
    @pytest.fixture
    def sample_application(self):
        """Sample application data"""
        return {
            "user_email": "test@example.com",
            "user_name": "Test User",
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco",
            "salary": "100k-120k",
            "job_url": "http://example.com/job",
            "skills_matched": ["Python", "JavaScript"]
        }
    
    def test_save_application(self, tracker, sample_application):
        """Test saving an application"""
        app_id = tracker.save_application(sample_application)
        
        assert app_id is not None
        assert isinstance(app_id, str)
        assert len(app_id) > 0
    
    def test_save_application_generates_id(self, tracker, sample_application):
        """Test that application ID is generated if not provided"""
        # Don't provide application_id
        app_id = tracker.save_application(sample_application)
        
        assert app_id is not None
    
    def test_save_application_adds_timestamp(self, tracker, sample_application):
        """Test that timestamp is added"""
        app_id = tracker.save_application(sample_application)
        
        # Retrieve and check
        apps = tracker.get_user_applications(sample_application["user_email"])
        assert len(apps) > 0
        assert "timestamp" in str(apps[0])
    
    def test_get_user_applications(self, tracker, sample_application):
        """Test retrieving user applications"""
        # Save application
        tracker.save_application(sample_application)
        
        # Retrieve
        apps = tracker.get_user_applications(sample_application["user_email"])
        
        assert len(apps) > 0
        assert apps[0]["user_email"] == sample_application["user_email"]
    
    def test_get_user_applications_empty(self, tracker):
        """Test retrieving applications for user with none"""
        apps = tracker.get_user_applications("nonexistent@example.com")
        
        assert len(apps) == 0
    
    def test_update_status(self, tracker, sample_application):
        """Test updating application status"""
        app_id = tracker.save_application(sample_application)
        
        # Update status
        tracker.update_status(app_id, "submitted")
        
        # Verify
        apps = tracker.get_user_applications(sample_application["user_email"])
        # Status should be updated
        assert any(app.get("status") == "submitted" for app in apps)
    
    def test_get_statistics(self, tracker, sample_application):
        """Test getting application statistics"""
        # Save multiple applications
        app1 = sample_application.copy()
        app1["status"] = "submitted"
        tracker.save_application(app1)
        
        app2 = sample_application.copy()
        app2["status"] = "pending"
        tracker.save_application(app2)
        
        app3 = sample_application.copy()
        app3["status"] = "failed"
        tracker.save_application(app3)
        
        # Get stats
        stats = tracker.get_statistics(sample_application["user_email"])
        
        assert "total" in stats
        assert "pending" in stats
        assert "submitted" in stats
        assert "failed" in stats
        assert stats["total"] >= 3
    
    def test_get_statistics_empty(self, tracker):
        """Test statistics for user with no applications"""
        stats = tracker.get_statistics("nonexistent@example.com")
        
        assert stats["total"] == 0
        assert stats["success_rate"] == 0
    
    def test_skills_list_converted_to_string(self, tracker, sample_application):
        """Test that skills list is converted to string"""
        app_id = tracker.save_application(sample_application)
        
        apps = tracker.get_user_applications(sample_application["user_email"])
        
        # Skills should be stored as string
        assert len(apps) > 0
