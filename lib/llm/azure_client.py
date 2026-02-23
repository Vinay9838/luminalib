import logging

from openai import AzureOpenAI
from django.conf import settings

from .base import BaseLLM

logger = logging.getLogger(__name__)


class AzureOpenAIClient(BaseLLM):

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )

        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    def generate_summary(self, text: str) -> str:
        logger.info("Generating summary using Azure OpenAI")
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional book summarizer. "
                        "Return ONLY the final summary text. "
                        "Do NOT include any introductory phrases, explanations, or comments. "
                        "Do NOT say things like 'Here is the summary'. "
                        "Just output the summary directly."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Summarize the following text in approximately 300 words. "
                        "Return only the summary content.\n\n"
                        f"{text}"
                    )
                }
            ],
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()

    def analyze_sentiment(self, text: str) -> float:
        logger.info("Analyzing sentiment using Azure OpenAI")
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sentiment analysis engine. "
                        "Return ONLY a single numeric value between -1 and 1. "
                        "-1 = very negative, "
                        "0 = neutral, "
                        "1 = very positive. "
                        "Do NOT return explanations. "
                        "Do NOT return text. "
                        "Return ONLY the numeric value."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the sentiment of the following text:\n\n"
                        f"{text}"
                    )
                }
            ],
            temperature=0,
        )

        return float(response.choices[0].message.content.strip())
    
    
    def generate_review_consensus(self, review_text: str) -> str:
        logger.info("Generating review consensus using Azure OpenAI")

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert analyst summarizing user feedback. "
                        "Analyze reviews and return ONLY a JSON object with the following structure:\n\n"
                        "{\n"
                        '  "overall_sentiment": "positive | neutral | negative",\n'
                        '  "key_praises": ["point1", "point2", "point3"],\n'
                        '  "key_criticisms": ["point1", "point2", "point3"]\n'
                        "}\n\n"
                        "Do NOT include explanations. "
                        "Do NOT include extra text. "
                        "Return ONLY valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the following user reviews and produce a consensus summary:\n\n"
                        f"{review_text}"
                    )
                }
            ],
            temperature=0.4,
        )

        return response.choices[0].message.content.strip()