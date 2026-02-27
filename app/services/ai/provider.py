"""
Provider abstraction layer.

Every LLM provider implements AIProvider. The factory resolves the configured
default or an explicitly requested provider at runtime.

Adding a new provider:
  1. Create app/services/ai/providers/my_provider.py
  2. Implement AIProvider
  3. Register in ProviderFactory
"""

from abc import ABC, abstractmethod
from typing import Any, Literal, Type

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ProviderName = Literal["openai", "anthropic", "gemini"]


class AIProvider(ABC):
    """Contract every provider must satisfy."""

    @property
    @abstractmethod
    def name(self) -> ProviderName:
        ...

    @abstractmethod
    def get_llm(self, temperature: float = 0.3, **kwargs: Any) -> BaseChatModel:
        """Return a LangChain chat model instance."""
        ...

    async def generate_structured(
        self,
        messages: list[dict],
        output_schema: Type[BaseModel],
        temperature: float = 0.3,
    ) -> BaseModel:
        """
        Call the LLM and parse a structured Pydantic response.
        Providers may override for provider-specific optimisations.
        """
        llm = self.get_llm(temperature=temperature)
        structured_llm = llm.with_structured_output(output_schema)
        from langchain_core.messages import HumanMessage, SystemMessage

        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            else:
                lc_messages.append(HumanMessage(content=msg["content"]))

        result = await structured_llm.ainvoke(lc_messages)
        return result  # type: ignore[return-value]


class ProviderFactory:
    _registry: dict[ProviderName, type["AIProvider"]] = {}

    @classmethod
    def register(cls, name: ProviderName):
        """Decorator to register a provider implementation."""
        def decorator(provider_cls: type):
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def get(cls, name: ProviderName | None = None) -> AIProvider:
        settings = get_settings()
        resolved = name or settings.default_ai_provider
        if resolved not in cls._registry:
            raise ValueError(
                f"Provider '{resolved}' not registered. "
                f"Available: {list(cls._registry.keys())}"
            )
        provider = cls._registry[resolved]()
        logger.debug("provider_selected", provider=resolved)
        return provider

    @classmethod
    def all_providers(cls) -> list[AIProvider]:
        return [p() for p in cls._registry.values()]


# Import providers so they self-register via @ProviderFactory.register
def _bootstrap_providers() -> None:
    from app.services.ai.providers import (  # noqa: F401
        openai_provider,
        anthropic_provider,
        gemini_provider,
    )

_bootstrap_providers()
