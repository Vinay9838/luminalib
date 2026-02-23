import logging
import requests
import json
from django.conf import settings

from .base import BaseLLM

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLM):

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def _generate(self, prompt: str, temperature: float):
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": "phi3",  # or hardcoded model
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 256,
                },
            },
            timeout=600,
        )

        response.raise_for_status()
        return response.json().get("response", "").strip()

    def generate_summary(self, text: str) -> str:
        prompt = f"""
            You are a professional book summarizer.

            Generate an approximately 300-word summary of the following content.

            IMPORTANT:
            - Output ONLY the summary text.
            - Do NOT include explanations.
            - Do NOT include introductory phrases.
            - Do NOT mention word count.
            - Do NOT add commentary.
            - Do NOT include titles or headings.

            Content:
            {text}
            """

        return self._generate(prompt, temperature=0.3)

    def analyze_sentiment(self, text: str) -> float:
        prompt = f"""
            You are a sentiment analysis engine.

            Return ONLY a single numeric value between -1 and 1.
            -1 = very negative
            0 = neutral
            1 = very positive

            IMPORTANT:
            - Return ONLY the numeric value.
            - Do NOT include text.
            - Do NOT include explanation.
            - Use at most two decimal places.

            Text:
            {text}
            """

        result = self._generate(prompt, temperature=0)

        try:
            return float(result.strip())
        except ValueError:
            logger.warning("Invalid sentiment response from Ollama: %s", result)
            return 0.0

    def generate_review_consensus(self, review_text: str) -> dict:
        prompt = f"""
            You are an expert analyst summarizing user feedback.

            Analyze the following reviews and return ONLY valid JSON
            with the exact structure below:

            {{
            "overall_sentiment": "positive | neutral | negative",
            "key_praises": ["point1", "point2", "point3"],
            "key_criticisms": ["point1", "point2", "point3"]
            }}

            IMPORTANT:
            - Return ONLY valid JSON.
            - Do NOT include explanation.
            - Do NOT include extra text.
            - Do NOT include markdown formatting.

            Reviews:
            {review_text}
            """

        result = self._generate(prompt, temperature=0)

        try:
            return json.loads(result)
        except Exception:
            logger.warning("Invalid consensus JSON from Ollama: %s", result)
            return {
                "overall_sentiment": "neutral",
                "key_praises": [],
                "key_criticisms": [],
            }
