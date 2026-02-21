from django.conf import settings
from .azure_client import AzureOpenAIClient



def get_llm_client():
    provider = settings.LLM_PROVIDER

    if provider == "azure":
        return AzureOpenAIClient()

    # elif provider == "local":
    #     return LocalLLMClient()

    raise ValueError("Invalid LLM provider configured.")