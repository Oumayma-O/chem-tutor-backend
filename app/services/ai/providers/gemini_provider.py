from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.services.ai.provider import AIProvider, ProviderFactory


@ProviderFactory.register("gemini")
class GeminiProvider(AIProvider):
    @property
    def name(self):
        return "gemini"

    def get_llm(self, temperature: float = 0.3, **kwargs: Any) -> ChatGoogleGenerativeAI:
        settings = get_settings()
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=temperature,
            **kwargs,
        )
