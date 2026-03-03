"""
Reference Card generation service.

Uses a few-shot LangChain chain with structured output.
The result is meant to be generated ONCE per topic and persisted in the DB.
"""

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.domain.schemas.tutor.problems import ReferenceCardOutput
from app.services.ai.llm import get_llm
from app.services.ai.reference_card.prompts import FEW_SHOT_EXAMPLES, REFERENCE_CARD_SYSTEM


async def generate_reference_card(
    topic_name: str,
    chapter_id: str,
    topic_index: int,
    key_equations: list[str] | None = None,
) -> ReferenceCardOutput:
    """
    Call the LLM chain to generate a conceptual reference card for a topic.

    Args:
        topic_name:    Human-readable topic name, e.g. "Zero-Order Kinetics".
        chapter_id:    Chapter slug, e.g. "chemical-kinetics".
        topic_index:   0-based topic index within the chapter.
        key_equations: Optional list of canonical equations stored on the Topic
                       row — injected into the prompt so the LLM uses them verbatim.

    Returns:
        A validated ReferenceCardOutput instance.
    """
    llm = get_llm(fast=True, temperature=0.1)
    structured_llm = llm.with_structured_output(ReferenceCardOutput)

    equation_hint = ""
    if key_equations:
        formatted = " | ".join(key_equations)
        equation_hint = f"\n\nKey equation(s) to use verbatim in the Equation step: {formatted}"

    user_prompt = (
        f"Generate a reference card for topic '{topic_name}' "
        f"(chapter_id='{chapter_id}', topic_index={topic_index}).{equation_hint}"
    )

    # Build few-shot message sequence
    messages: list = [SystemMessage(content=REFERENCE_CARD_SYSTEM)]
    for ex in FEW_SHOT_EXAMPLES:
        messages.append(HumanMessage(content=ex["human"]))
        messages.append(AIMessage(content=ex["assistant"]))
    messages.append(HumanMessage(content=user_prompt))

    result: ReferenceCardOutput = await structured_llm.ainvoke(messages)
    # Ensure metadata fields match the request (guard against hallucination)
    result.chapter_id = chapter_id
    result.topic_index = topic_index
    return result
