"""
OpenAI Helper Module
Provides optional GPT integration for chat responses, skill extraction, and recommendation explanations.
Falls back gracefully when OpenAI is unconfigured or unavailable.
"""

import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class OpenAIHelper:
    """Optional OpenAI GPT integration for enhanced NLP capabilities"""

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini",
                 max_tokens: int = 512, temperature: float = 0.7):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.available = False
        self.client = None

        if not api_key:
            logger.info("OpenAI API key not provided – GPT features disabled")
            return

        if OpenAI is None:
            logger.warning("openai package not installed – GPT features disabled")
            return

        try:
            self.client = OpenAI(api_key=api_key)
            self.available = True
            logger.info("OpenAI helper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def generate_chat_response(self, user_message: str,
                               extracted_skills: List[str],
                               session_context: Optional[Dict] = None) -> Optional[str]:
        """
        Generate a conversational chat response using GPT.

        Args:
            user_message: The user's chat message
            extracted_skills: Skills extracted from the message
            session_context: Optional dict with prior conversation context

        Returns:
            Generated response string, or None on any failure
        """
        if not self.available:
            return None

        try:
            skills_text = ", ".join(extracted_skills) if extracted_skills else "none detected"
            system_prompt = (
                "You are a friendly career advisor chatbot. "
                "Keep responses to 2-4 sentences. "
                "Acknowledge any skills the user mentions and ask a relevant follow-up question "
                "to better understand their career goals or experience."
            )
            user_content = f"User message: {user_message}\nExtracted skills: {skills_text}"

            if session_context and session_context.get("last_message"):
                user_content += f"\nPrevious message: {session_context['last_message']}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat response error: {e}")
            return None

    def extract_skills_gpt(self, text: str,
                           known_skills: Optional[List[str]] = None) -> Optional[List[str]]:
        """
        Extract skills from text using GPT.

        Args:
            text: Input text to extract skills from
            known_skills: Optional list of known skill names as hints

        Returns:
            List of extracted skill name strings, or None on any failure
        """
        if not self.available:
            return None

        try:
            known_hint = ""
            if known_skills:
                sample = known_skills[:100]
                known_hint = (
                    f"\nHere are some known skills for reference (not a hard constraint): "
                    f"{', '.join(sample)}"
                )

            system_prompt = (
                "You are a skill extraction engine. "
                "Given user text, return a JSON array of skill name strings found in the text. "
                "Only return the JSON array, no other text."
                f"{known_hint}"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            skills = json.loads(content)
            if isinstance(skills, list) and all(isinstance(s, str) for s in skills):
                return skills

            logger.warning("OpenAI skill extraction returned unexpected format")
            return None
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"OpenAI skill extraction parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"OpenAI skill extraction error: {e}")
            return None

    def generate_recommendation_explanation(self, score: float,
                                            matching_skills: List[str],
                                            missing_skills: List[str],
                                            user_profile: Dict,
                                            job: Dict) -> Optional[str]:
        """
        Generate a personalized recommendation explanation using GPT.

        Args:
            score: Match score (0-100)
            matching_skills: Skills the user has that match the job
            missing_skills: Skills the user is missing for the job
            user_profile: User profile dictionary
            job: Job dictionary

        Returns:
            Explanation string, or None on any failure
        """
        if not self.available:
            return None

        try:
            system_prompt = (
                "You are a career advisor. Write a 2-3 sentence personalized explanation "
                "for why a job is a good or poor match for a candidate. Be specific and encouraging."
            )
            user_content = (
                f"Match score: {score:.0f}/100\n"
                f"Matching skills: {', '.join(matching_skills) if matching_skills else 'none'}\n"
                f"Missing skills: {', '.join(missing_skills) if missing_skills else 'none'}\n"
                f"Experience: {user_profile.get('experience_years', 0)} years\n"
                f"Job title: {job.get('title', 'Unknown')}\n"
                f"Company: {job.get('company', 'Unknown')}"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                max_tokens=200,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI recommendation explanation error: {e}")
            return None
