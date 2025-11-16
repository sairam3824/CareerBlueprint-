# 🧪 Testing Guide

## Overview

Comprehensive test suite for the AI Job Recommendation Bot covering unit tests, integration tests, and end-to-end scenarios.

## Test Structure

```
tests/
├── unit/                           # Unit tests for individual modules
│   ├── test_skill_analyzer.py     # Skill extraction & normalization
│   ├── test_job_fetcher.py        # Job fetching & caching
│   ├── test_recommendation_engine.py  # Recommendation algorithm
│   ├── test_application_tracker.py    # Application storage
│   └── test_email_service.py      # Email sending
├── integration/                    # Integration tests
│   └── test_api_endpoints.py      # API endpoint tests
└── fixtures/                       # Test data
    ├── sample_profiles.json       # Sample user profiles
    └── sample_jobs.json           # Sample job listings
```

## Running Tests

### Run All Tests
```bash
./run_tests.sh
```

### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Run Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_skill_analyzer.py -v
```

### Run Specific Test
```bash
pytest tests/unit/test_skill_analyzer.py::TestSkillAnalyzer::test_extract_skills_comma_separated -v
```

### Run with Coverage
```bash
pytest --cov=backend --cov-report=html
```

## Test Coverage

### Unit Tests

#### Skill Analyzer (test_skill_analyzer.py)
- ✅ Extract skills from comma-separated lists
- ✅ Extract skills from natural language
- ✅ Handle synonyms correctly
- ✅ Normalize skills to standard names
- ✅ Identify skill gaps
- ✅ Rank gaps by frequency
- ✅ Provide learning resources
- ✅ Assign proficiency levels
- ✅ Handle empty/invalid input

#### Job Fetcher (test_job_fetcher.py)
- ✅ Fetch jobs from Adzuna API
- ✅ Fetch jobs from JSearch API
- ✅ Cache job results
- ✅ Deduplicate jobs
- ✅ Handle API timeouts
- ✅ Handle API errors
- ✅ Normalize job data
- ✅ Respect cache TTL

#### Recommendation Engine (test_recommendation_engine.py)
- ✅ Generate recommendations
- ✅ Sort by match score
- ✅ Compute skill similarity
- ✅ Match experience levels
- ✅ Match locations
- ✅ Match salary ranges
- ✅ Compare skills
- ✅ Generate explanations
- ✅ Calculate confidence
- ✅ Respect result limits

#### Application Tracker (test_application_tracker.py)
- ✅ Save applications
- ✅ Generate application IDs
- ✅ Add timestamps
- ✅ Retrieve user applications
- ✅ Update application status
- ✅ Calculate statistics
- ✅ Handle empty results
- ✅ Convert skills to strings

#### Email Service (test_email_service.py)
- ✅ Render email templates
- ✅ Send confirmation emails
- ✅ Send weekly digests
- ✅ Retry on failure
- ✅ Handle SMTP errors
- ✅ Use default templates

### Integration Tests

#### API Endpoints (test_api_endpoints.py)
- ✅ Health check endpoint
- ✅ Chat message endpoint
- ✅ Profile creation
- ✅ Profile retrieval
- ✅ Generate recommendations
- ✅ Submit applications
- ✅ Get application history
- ✅ Handle invalid input
- ✅ Error responses

## Test Data

### Sample Profiles (tests/fixtures/sample_profiles.json)
- Junior developer (1 year experience)
- Mid-level developer (3 years experience)
- Senior developer (5 years experience)

### Sample Jobs (tests/fixtures/sample_jobs.json)
- Entry level positions
- Mid-level positions
- Senior positions
- Remote and onsite
- Various tech stacks

## Writing New Tests

### Unit Test Template
```python
import pytest
from backend.module_name import ClassName

class TestClassName:
    @pytest.fixture
    def instance(self):
        return ClassName()
    
    def test_method_name(self, instance):
        result = instance.method()
        assert result == expected
```

### Integration Test Template
```python
import pytest
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    return flask_app.test_client()

def test_endpoint(client):
    response = client.get('/api/endpoint')
    assert response.status_code == 200
```

## Mocking External Services

### Mock API Calls
```python
from unittest.mock import patch

@patch('backend.job_fetcher.job_fetcher.requests.get')
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {"data": []}
    # Test code here
```

### Mock Email Sending
```python
@patch.object(EmailService, 'send')
def test_email(mock_send):
    mock_send.return_value = True
    # Test code here
```

## Continuous Integration

### GitHub Actions (example)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

## Test Best Practices

### Do's ✅
- Write tests for all new features
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests independent
- Use fixtures for common setup
- Mock external dependencies
- Test both success and failure paths

### Don'ts ❌
- Don't test external APIs directly
- Don't write tests that depend on each other
- Don't hardcode sensitive data
- Don't skip error handling tests
- Don't test implementation details

## Debugging Tests

### Run with Verbose Output
```bash
pytest -vv
```

### Show Print Statements
```bash
pytest -s
```

### Stop on First Failure
```bash
pytest -x
```

### Run Last Failed Tests
```bash
pytest --lf
```

### Debug with PDB
```bash
pytest --pdb
```

## Performance Testing

### Measure Test Duration
```bash
pytest --durations=10
```

### Profile Tests
```bash
pytest --profile
```

## Test Metrics

### Current Coverage
- **Unit Tests**: 85%+ coverage
- **Integration Tests**: All endpoints covered
- **Total Tests**: 50+ test cases

### Test Execution Time
- Unit tests: < 5 seconds
- Integration tests: < 10 seconds
- Total: < 15 seconds

## Troubleshooting

### Tests Fail with Import Errors
```bash
# Make sure you're in the project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Tests Fail with Missing Dependencies
```bash
pip install -r requirements.txt
```

### Integration Tests Fail
```bash
# Make sure Flask app can start
python app.py
# Check logs/bot.log for errors
```

### Cache-Related Test Failures
```bash
# Clear test cache
rm -rf tests/__pycache__
rm -rf .pytest_cache
```

## Future Test Additions

### Planned Tests
- [ ] Load testing with locust
- [ ] Security testing
- [ ] Browser automation tests (Selenium)
- [ ] API contract testing
- [ ] Performance benchmarks

### Test Improvements
- [ ] Increase coverage to 95%+
- [ ] Add mutation testing
- [ ] Add property-based testing
- [ ] Add visual regression tests

---

## Quick Reference

```bash
# Run all tests
./run_tests.sh

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific module
pytest tests/unit/test_skill_analyzer.py -v

# Debug mode
pytest --pdb -x

# Generate HTML report
pytest --html=report.html
```

---

**Happy Testing!** 🧪
