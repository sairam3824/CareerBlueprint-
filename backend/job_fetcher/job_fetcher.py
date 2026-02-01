"""
Job Fetcher Module
Fetches jobs from multiple APIs, caches results, and deduplicates
"""

import requests
import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class AdzunaClient:
    """Client for Adzuna Job Search API"""
    
    def __init__(self, app_id: str, app_key: str, base_url: str = "https://api.adzuna.com/v1/api"):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = base_url
        self.timeout = 5
    
    def search_jobs(self, query: str, location: str = "us", limit: int = 50) -> List[Dict]:
        """
        Search for jobs on Adzuna
        
        Args:
            query: Search query (skills, job title)
            location: Country code (us, uk, etc.)
            limit: Maximum number of results
            
        Returns:
            List of job dictionaries
        """
        try:
            url = f"{self.base_url}/jobs/{location}/search/1"
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": min(limit, 50),
                "what": query,
                "content-type": "application/json"
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get("results", []):
                job = self._normalize_job(result)
                jobs.append(job)
            
            return jobs
            
        except requests.Timeout:
            logger.warning(f"Adzuna API timeout after {self.timeout}s")
            return []
        except requests.RequestException as e:
            logger.error(f"Adzuna API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Adzuna client: {e}")
            return []
    
    def _normalize_job(self, raw_job: Dict) -> Dict:
        """Normalize Adzuna job data to standard format"""
        return {
            "id": raw_job.get("id", ""),
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company", {}).get("display_name", "Unknown"),
            "location": raw_job.get("location", {}).get("display_name", ""),
            "remote": "remote" in raw_job.get("title", "").lower() or 
                     "remote" in raw_job.get("description", "").lower(),
            "description": raw_job.get("description", ""),
            "requirements": self._extract_requirements(raw_job.get("description", "")),
            "salary_min": raw_job.get("salary_min"),
            "salary_max": raw_job.get("salary_max"),
            "currency": "USD",
            "url": raw_job.get("redirect_url", ""),
            "posted_date": raw_job.get("created", ""),
            "source": "adzuna"
        }
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract skill requirements from job description"""
        # Simple keyword extraction
        skills = []
        common_skills = [
            "python", "javascript", "java", "react", "angular", "vue",
            "node.js", "docker", "kubernetes", "aws", "azure", "gcp",
            "sql", "mongodb", "postgresql", "git", "agile", "scrum"
        ]
        
        desc_lower = description.lower()
        for skill in common_skills:
            if skill in desc_lower:
                skills.append(skill.title())
        
        return skills


class JSearchClient:
    """Client for JSearch API via RapidAPI"""
    
    def __init__(self, api_key: str, base_url: str = "https://jsearch.p.rapidapi.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = 5
    
    def search_jobs(self, query: str, location: str = "United States", limit: int = 50) -> List[Dict]:
        """
        Search for jobs on JSearch
        
        Args:
            query: Search query (skills, job title)
            location: Location string
            limit: Maximum number of results
            
        Returns:
            List of job dictionaries
        """
        try:
            url = f"{self.base_url}/search"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            params = {
                "query": f"{query} in {location}",
                "num_pages": "1",
                "page": "1"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get("data", [])[:limit]:
                job = self._normalize_job(result)
                jobs.append(job)
            
            return jobs
            
        except requests.Timeout:
            logger.warning(f"JSearch API timeout after {self.timeout}s")
            return []
        except requests.RequestException as e:
            logger.error(f"JSearch API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in JSearch client: {e}")
            return []
    
    def _normalize_job(self, raw_job: Dict) -> Dict:
        """Normalize JSearch job data to standard format"""
        return {
            "id": raw_job.get("job_id", ""),
            "title": raw_job.get("job_title", ""),
            "company": raw_job.get("employer_name", "Unknown"),
            "location": raw_job.get("job_city", "") + ", " + raw_job.get("job_state", ""),
            "remote": raw_job.get("job_is_remote", False),
            "description": raw_job.get("job_description", ""),
            "requirements": raw_job.get("job_required_skills", []),
            "salary_min": raw_job.get("job_min_salary"),
            "salary_max": raw_job.get("job_max_salary"),
            "currency": "USD",
            "url": raw_job.get("job_apply_link", ""),
            "posted_date": raw_job.get("job_posted_at_datetime_utc", ""),
            "source": "jsearch"
        }


class JobCache:
    """Simple file-based cache for job listings"""
    
    def __init__(self, cache_dir: str = "./data/cache", ttl_hours: int = 6):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def get(self, key: str) -> Optional[List[Dict]]:
        """Get cached jobs if not expired"""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cached_time > self.ttl:
                # Cache expired
                cache_file.unlink()
                return None
            
            return data["jobs"]
            
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def set(self, key: str, jobs: List[Dict]):
        """Cache jobs with timestamp"""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.json"
        
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "key": key,
                "jobs": jobs
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key"""
        return hashlib.md5(key.encode()).hexdigest()


class JobFetcher:
    """Main job fetcher that aggregates from multiple sources"""
    
    def __init__(self, config: Dict):
        self.adzuna_client = None
        self.jsearch_client = None
        
        # Initialize clients if credentials provided
        if config.get("adzuna_app_id") and config.get("adzuna_app_key"):
            self.adzuna_client = AdzunaClient(
                config["adzuna_app_id"],
                config["adzuna_app_key"]
            )
        
        if config.get("rapidapi_key"):
            self.jsearch_client = JSearchClient(config["rapidapi_key"])
        
        self.cache = JobCache(ttl_hours=config.get("cache_ttl_hours", 6))
    
    def fetch_jobs(self, query: str, location: str = "", limit: int = 50) -> List[Dict]:
        """
        Fetch jobs from all available sources
        
        Args:
            query: Search query (skills, job title)
            location: Location string
            limit: Maximum number of results
            
        Returns:
            List of deduplicated job dictionaries
        """
        # Check cache first
        cache_key = f"{query}_{location}_{limit}"
        cached_jobs = self.cache.get(cache_key)
        if cached_jobs:
            logger.info(f"Returning {len(cached_jobs)} jobs from cache")
            return cached_jobs
        
        all_jobs = []
        
        # Fetch from Adzuna
        if self.adzuna_client:
            try:
                adzuna_jobs = self.adzuna_client.search_jobs(query, "us", limit)
                all_jobs.extend(adzuna_jobs)
                logger.info(f"Fetched {len(adzuna_jobs)} jobs from Adzuna")
            except Exception as e:
                logger.error(f"Adzuna fetch failed: {e}")
        
        # Fetch from JSearch
        if self.jsearch_client:
            try:
                jsearch_jobs = self.jsearch_client.search_jobs(query, location or "United States", limit)
                all_jobs.extend(jsearch_jobs)
                logger.info(f"Fetched {len(jsearch_jobs)} jobs from JSearch")
            except Exception as e:
                logger.error(f"JSearch fetch failed: {e}")
        
        # Deduplicate
        deduplicated = self._deduplicate_jobs(all_jobs)
        
        # Cache results
        self.cache.set(cache_key, deduplicated)
        
        return deduplicated[:limit]
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a key from title and company (normalized)
            key = (
                job["title"].lower().strip(),
                job["company"].lower().strip()
            )
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
