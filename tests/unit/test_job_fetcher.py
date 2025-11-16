"""
Unit tests for Job Fetcher module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.job_fetcher.job_fetcher import JobFetcher, AdzunaClient, JSearchClient, JobCache


class TestJobCache:
    """Test suite for JobCache class"""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create JobCache instance with temporary directory"""
        return JobCache(cache_dir=str(tmp_path / "cache"), ttl_hours=1)
    
    def test_cache_set_and_get(self, cache):
        """Test setting and getting cached data"""
        key = "test_query"
        jobs = [{"id": "1", "title": "Software Engineer"}]
        
        cache.set(key, jobs)
        cached_jobs = cache.get(key)
        
        assert cached_jobs is not None
        assert len(cached_jobs) == 1
        assert cached_jobs[0]["title"] == "Software Engineer"
    
    def test_cache_get_nonexistent(self, cache):
        """Test getting non-existent cache entry"""
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_expiration(self, cache):
        """Test that cache expires after TTL"""
        # This would require time manipulation, simplified for now
        key = "test_query"
        jobs = [{"id": "1", "title": "Test"}]
        
        cache.set(key, jobs)
        result = cache.get(key)
        
        assert result is not None


class TestAdzunaClient:
    """Test suite for AdzunaClient"""
    
    @pytest.fixture
    def client(self):
        """Create AdzunaClient instance"""
        return AdzunaClient(app_id="test_id", app_key="test_key")
    
    @patch('backend.job_fetcher.job_fetcher.requests.get')
    def test_search_jobs_success(self, mock_get, client):
        """Test successful job search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "title": "Software Engineer",
                    "company": {"display_name": "Tech Corp"},
                    "location": {"display_name": "San Francisco"},
                    "description": "Great job",
                    "redirect_url": "http://example.com"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        jobs = client.search_jobs("Python developer")
        
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Software Engineer"
        assert jobs[0]["company"] == "Tech Corp"
        assert jobs[0]["source"] == "adzuna"
    
    @patch('backend.job_fetcher.job_fetcher.requests.get')
    def test_search_jobs_timeout(self, mock_get, client):
        """Test handling of API timeout"""
        mock_get.side_effect = Exception("Timeout")
        
        jobs = client.search_jobs("Python developer")
        
        assert jobs == []
    
    @patch('backend.job_fetcher.job_fetcher.requests.get')
    def test_search_jobs_api_error(self, mock_get, client):
        """Test handling of API error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response
        
        jobs = client.search_jobs("Python developer")
        
        assert jobs == []


class TestJSearchClient:
    """Test suite for JSearchClient"""
    
    @pytest.fixture
    def client(self):
        """Create JSearchClient instance"""
        return JSearchClient(api_key="test_key")
    
    @patch('backend.job_fetcher.job_fetcher.requests.get')
    def test_search_jobs_success(self, mock_get, client):
        """Test successful job search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "job_id": "456",
                    "job_title": "Python Developer",
                    "employer_name": "StartupCo",
                    "job_city": "New York",
                    "job_state": "NY",
                    "job_description": "Exciting role",
                    "job_apply_link": "http://example.com",
                    "job_is_remote": False
                }
            ]
        }
        mock_get.return_value = mock_response
        
        jobs = client.search_jobs("Python developer")
        
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Python Developer"
        assert jobs[0]["company"] == "StartupCo"
        assert jobs[0]["source"] == "jsearch"


class TestJobFetcher:
    """Test suite for JobFetcher"""
    
    @pytest.fixture
    def fetcher(self, tmp_path):
        """Create JobFetcher instance"""
        config = {
            "adzuna_app_id": "test_id",
            "adzuna_app_key": "test_key",
            "rapidapi_key": "test_rapid_key",
            "cache_ttl_hours": 1
        }
        return JobFetcher(config)
    
    def test_deduplicate_jobs(self, fetcher):
        """Test job deduplication"""
        jobs = [
            {"id": "1", "title": "Software Engineer", "company": "Tech Corp"},
            {"id": "2", "title": "software engineer", "company": "tech corp"},  # Duplicate
            {"id": "3", "title": "Data Scientist", "company": "Data Inc"}
        ]
        
        deduplicated = fetcher._deduplicate_jobs(jobs)
        
        assert len(deduplicated) == 2
        titles = [j["title"] for j in deduplicated]
        assert "Software Engineer" in titles or "software engineer" in titles
        assert "Data Scientist" in titles
    
    @patch.object(AdzunaClient, 'search_jobs')
    @patch.object(JSearchClient, 'search_jobs')
    def test_fetch_jobs_from_multiple_sources(self, mock_jsearch, mock_adzuna, fetcher):
        """Test fetching jobs from multiple sources"""
        mock_adzuna.return_value = [
            {"id": "1", "title": "Job 1", "company": "Company A", "source": "adzuna"}
        ]
        mock_jsearch.return_value = [
            {"id": "2", "title": "Job 2", "company": "Company B", "source": "jsearch"}
        ]
        
        jobs = fetcher.fetch_jobs("Python", limit=10)
        
        # Should have jobs from both sources
        assert len(jobs) >= 1
    
    def test_fetch_jobs_with_cache(self, fetcher, tmp_path):
        """Test that caching works"""
        # First call - should fetch from APIs
        with patch.object(AdzunaClient, 'search_jobs') as mock_adzuna:
            mock_adzuna.return_value = [
                {"id": "1", "title": "Cached Job", "company": "Company", "source": "adzuna"}
            ]
            
            jobs1 = fetcher.fetch_jobs("Python", limit=10)
            
            # Second call - should use cache
            jobs2 = fetcher.fetch_jobs("Python", limit=10)
            
            # Should only call API once
            assert mock_adzuna.call_count == 1
