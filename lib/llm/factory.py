from django.conf import settings

from .azure_client import AzureOpenAIClient
from .ollama_client import OllamaClient



def get_llm_client():
    provider = settings.LLM_PROVIDER

    if provider == "azure":
        return AzureOpenAIClient()

    if provider == "ollama":
        return OllamaClient()

    raise ValueError("Invalid LLM provider configured.")