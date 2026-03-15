"""
LLM factory — one module, two tiers.

  get_llm()          → powerful model  (problem generation)
  get_llm(fast=True) → lightweight model (hints, validation)

  generate_structured() → convenience wrapper: build LangChain messages,
                           call with_structured_output, return parsed result.

Provider and model names are read from .env via Settings.
LangChain already provides the provider abstraction — no extra layer needed.
"""

from typing import Any, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

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

    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=model, google_api_key=s.google_api_key, temperature=temperature)


async def generate_structured(
    messages: list[dict],
    output_schema: Type[BaseModel],
    temperature: float = 0.3,
    fast: bool = False,
) -> Any:
    """
    Call the configured LLM with structured output.

    Args:
        messages:      list of {"role": "system"|"user", "content": str}
        output_schema: Pydantic model class — LLM output is parsed into this
        temperature:   sampling temperature
        fast:          True → use the fast/cheap tier (hints, validation)

    Returns:
        A validated instance of output_schema.
    """
    llm = get_llm(fast=fast, temperature=temperature)
    # langchain-openai >= 0.3 defaults to method="json_schema" which uses the
    # OpenAI beta parse() API and returns a ParsedChatCompletion. LangChain then
    # calls model_dump() on it; because ParsedChatCompletion.parsed is typed as
    # Optional[TypeVar] (unresolved generic), Pydantic v2 sees it as None-type
    # and emits a serialization UserWarning on every call.
    # method="function_calling" uses the regular create() path (plain ChatCompletion,
    # no parsed field) and avoids the warning entirely.
    # Other providers (Anthropic, Gemini) don't accept a `method` kwarg.
    so_kwargs = {"method": "function_calling"} if "openai" in type(llm).__module__ else {}
    structured = llm.with_structured_output(output_schema, **so_kwargs)
    lc_messages = [
        SystemMessage(content=m["content"]) if m["role"] == "system" else HumanMessage(content=m["content"])
        for m in messages
    ]
    return await structured.ainvoke(lc_messages)
