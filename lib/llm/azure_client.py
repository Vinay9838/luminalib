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
                    "content": "You are a professional book summarizer."
                },
                {
                    "role": "user",
                    "content": f"Summarize the following text in 300 words:\n\n{text}"
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
                    "content": "Return only a sentiment score between -1, 0, and 1."
                },
                {
                    "role": "user",
                    "content": f"Analyze sentiment of this text:\n{text}"
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
                        "Provide a concise, structured summary of overall reader sentiment, "
                        "highlighting common praises and criticisms."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the following user reviews and produce a consensus summary:\n\n"
                        f"{review_text}"
                    ),
                },
            ],
            temperature=0.4,
        )

        return response.choices[0].message.content.strip()