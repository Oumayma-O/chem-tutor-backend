"""
LLM factory — one function, two tiers.

  get_llm()          → powerful model  (problem generation)
  get_llm(fast=True) → lightweight model (validation, hints)

Provider and model are read from .env via Settings.
LangChain already provides the provider abstraction — no extra layer needed.
"""

from langchain_core.language_models import BaseChatModel

from app.core.config import get_settings


def get_llm(fast: bool = False, temperature: float = 0.3) -> BaseChatModel:
    s = get_settings()
    provider = s.fast_ai_provider if fast else s.default_ai_provider
    model = {
        "openai":    s.fast_openai_model    if fast else s.openai_model,
        "anthropic": s.fast_anthropic_model if fast else s.anthropic_model,
        "gemini":    s.fast_gemini_model    if fast else s.gemini_model,
    }[provider]

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=s.openai_api_key, temperature=temperature)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=s.anthropic_api_key, temperature=temperature)

    # gemini (default)
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=model, google_api_key=s.google_api_key, temperature=temperature)
