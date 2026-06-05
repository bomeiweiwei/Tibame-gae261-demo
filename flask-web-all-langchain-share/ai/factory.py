from enums.ai_type import AiType

from ai.base import BaseAILangchain

from ai.lmstudio_langchain import LMStudioLangchain
from ai.azure_langchain import AzureLangchain
from ai.gemini_langchain import GeminiLangchain
from ai.ollama_langchain import OllamaLangchain

from core.config import get_settings


def create_ai_langchain(ai_type: AiType | str) -> BaseAILangchain:
    settings = get_settings()

    ai_type = AiType(ai_type)

    if ai_type == AiType.GEMINI:
        return GeminiLangchain(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model_name,
        )

    if ai_type == AiType.AZURE:
        return AzureLangchain(
            api_key=settings.azure_openai_api_key,
            endpoint=settings.azure_openai_endpoint,
            deployment_name=settings.azure_openai_deployment_name,
        )

    if ai_type == AiType.LMSTUDIO:
        return LMStudioLangchain(
            base_url=settings.lmstudio_base_url,
            api_key=settings.lmstudio_api_key,
            model_name=settings.lmstudio_model_name,
        )
    
    if ai_type == AiType.OLLAMA:
        return OllamaLangchain(
            model_name=settings.ollama_model_name,
        )

    raise ValueError(f"不支援的 AI 類型：{ai_type}")
