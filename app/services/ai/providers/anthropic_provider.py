from typing import Any

from langchain_anthropic import ChatAnthropic

from app.core.config import get_settings
from app.services.ai.provider import AIProvider, ProviderFactory


@ProviderFactory.register("anthropic")
class AnthropicProvider(AIProvider):
    @property
    def name(self):
        return "anthropic"

    def get_llm(self, temperature: float = 0.3, **kwargs: Any) -> ChatAnthropic:
        settings = get_settings()
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            **kwargs,
        )
