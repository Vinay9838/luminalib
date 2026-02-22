import logging
import requests
from django.conf import settings

from .base import BaseLLM

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLM):

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def _generate(self, prompt: str, temperature: float = 0.5) -> str:
        logger.info("Calling Ollama model: %s", self.model)

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 256,
                }
            },
            timeout=600,
        )

        response.raise_for_status()

        return response.json()["response"].strip()

    def generate_summary(self, text: str) -> str:
        prompt = f"""
        You are a professional book summarizer.
        Summarize the following text in 300 words:

        {text}
        """
        return self._generate(prompt, temperature=0.5)

    def analyze_sentiment(self, text: str) -> float:
        prompt = f"""
        Return only a sentiment score between -1 and 1.
        Text:
        {text}
        """

        result = self._generate(prompt, temperature=0)

        try:
            return float(result)
        except ValueError:
            logger.warning("Invalid sentiment response from Ollama: %s", result)
            return 0.0

    def generate_review_consensus(self, review_text: str) -> str:
        prompt = f"""
        Provide a concise consensus summary of the following user reviews.
        Highlight common praises and criticisms.

        {review_text}
        """

        return self._generate(prompt, temperature=0.4)
