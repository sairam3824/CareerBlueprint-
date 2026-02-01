"""
Unit tests for OpenAIHelper
Tests disabled/fallback behavior and JSON parsing edge cases.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from backend.openai_helper.openai_helper import OpenAIHelper


class TestOpenAIHelperDisabled:
    """Tests when OpenAI is not configured"""

    def test_available_false_when_no_api_key(self):
        helper = OpenAIHelper(api_key="")
        assert helper.available is False

    def test_available_false_when_api_key_none(self):
        helper = OpenAIHelper(api_key="")
        assert helper.available is False
        assert helper.client is None

    def test_generate_chat_response_returns_none_when_disabled(self):
        helper = OpenAIHelper(api_key="")
        result = helper.generate_chat_response("hello", ["Python"])
        assert result is None

    def test_extract_skills_gpt_returns_none_when_disabled(self):
        helper = OpenAIHelper(api_key="")
        result = helper.extract_skills_gpt("I know Python and React")
        assert result is None

    def test_generate_recommendation_explanation_returns_none_when_disabled(self):
        helper = OpenAIHelper(api_key="")
        result = helper.generate_recommendation_explanation(
            score=85.0,
            matching_skills=["Python"],
            missing_skills=["Go"],
            user_profile={"experience_years": 3},
            job={"title": "Backend Dev", "company": "Acme"},
        )
        assert result is None


class TestOpenAIHelperNoPackage:
    """Tests when openai package is not installed"""

    def test_available_false_when_package_missing(self):
        with patch("backend.openai_helper.openai_helper.OpenAI", None):
            helper = OpenAIHelper(api_key="sk-test-key")
            assert helper.available is False


class TestOpenAIHelperEnabled:
    """Tests with a mocked OpenAI client"""

    def _make_helper(self):
        """Create a helper with mocked client"""
        helper = OpenAIHelper(api_key="")
        helper.client = MagicMock()
        helper.available = True
        return helper

    def _mock_response(self, content):
        """Create a mock chat completion response"""
        choice = MagicMock()
        choice.message.content = content
        response = MagicMock()
        response.choices = [choice]
        return response

    def test_generate_chat_response_success(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.return_value = self._mock_response(
            "Great, you know Python! What kind of roles interest you?"
        )
        result = helper.generate_chat_response("I know Python", ["Python"])
        assert result == "Great, you know Python! What kind of roles interest you?"

    def test_generate_chat_response_api_error_returns_none(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.side_effect = Exception("API error")
        result = helper.generate_chat_response("hello", [])
        assert result is None

    def test_extract_skills_gpt_valid_json(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.return_value = self._mock_response(
            '["Python", "React", "Docker"]'
        )
        result = helper.extract_skills_gpt("I work with Python, React and Docker")
        assert result == ["Python", "React", "Docker"]

    def test_extract_skills_gpt_code_fenced_json(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.return_value = self._mock_response(
            '```json\n["Python", "React"]\n```'
        )
        result = helper.extract_skills_gpt("I know Python and React")
        assert result == ["Python", "React"]

    def test_extract_skills_gpt_invalid_json_returns_none(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.return_value = self._mock_response(
            "Here are the skills: Python, React"
        )
        result = helper.extract_skills_gpt("I know Python and React")
        assert result is None

    def test_extract_skills_gpt_non_list_json_returns_none(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.return_value = self._mock_response(
            '{"skills": ["Python"]}'
        )
        result = helper.extract_skills_gpt("I know Python")
        assert result is None

    def test_extract_skills_gpt_non_string_items_returns_none(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.return_value = self._mock_response(
            '[1, 2, 3]'
        )
        result = helper.extract_skills_gpt("test")
        assert result is None

    def test_extract_skills_gpt_api_error_returns_none(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.side_effect = Exception("timeout")
        result = helper.extract_skills_gpt("I know Python")
        assert result is None

    def test_extract_skills_gpt_empty_array(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.return_value = self._mock_response("[]")
        result = helper.extract_skills_gpt("no skills here")
        assert result == []

    def test_generate_recommendation_explanation_success(self):
        helper = self._make_helper()
        explanation = "This role is a strong match given your Python expertise."
        helper.client.chat.completions.create.return_value = self._mock_response(
            explanation
        )
        result = helper.generate_recommendation_explanation(
            score=85.0,
            matching_skills=["Python"],
            missing_skills=["Go"],
            user_profile={"experience_years": 3},
            job={"title": "Backend Dev", "company": "Acme"},
        )
        assert result == explanation

    def test_generate_recommendation_explanation_api_error_returns_none(self):
        helper = self._make_helper()
        helper.client.chat.completions.create.side_effect = Exception("API error")
        result = helper.generate_recommendation_explanation(
            score=50.0,
            matching_skills=[],
            missing_skills=["Java"],
            user_profile={},
            job={"title": "Dev"},
        )
        assert result is None
