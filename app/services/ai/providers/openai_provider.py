from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.services.ai.provider import AIProvider, ProviderFactory


@ProviderFactory.register("openai")
class OpenAIProvider(AIProvider):
    @property
    def name(self):
        return "openai"

    def get_llm(self, temperature: float = 0.3, **kwargs: Any) -> ChatOpenAI:
        settings = get_settings()
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
            **kwargs,
        )
