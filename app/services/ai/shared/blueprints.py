"""
Shared blueprint definitions — single source of truth for both
problem generation and reference card generation.

Importing from here guarantees that step labels, step counts, logic
descriptions, and skill lists stay in sync across all AI services.
"""

from typing import Literal

BlueprintName = Literal["solver", "recipe", "architect", "detective", "lawyer"]
Tool = Literal["calculator", "periodic_table"]

BLUEPRINT_CONFIG: dict[str, dict] = {
    "solver": {
        "step_count": 5,
        "labels": ["Equation", "Knowns", "Substitute", "Calculate", "Answer"],
        "logic": "Input variables -> Formula -> Result.",
    },
    "recipe": {
        "step_count": 5,
        "labels": ["Goal / Setup", "Conversion Factors", "Dimensional Setup", "Calculate", "Answer"],
        "logic": "Series of conversions where the output of A is the input of B.",
    },
    "architect": {
        "step_count": 4,
        "labels": ["Inventory / Rules", "Draft", "Refine", "Final Answer"],
        "logic": "Building a symbolic representation based on rules.",
    },
    "detective": {
        "step_count": 4,
        "labels": ["Data Extraction", "Feature ID", "Apply Concept", "Conclusion"],
        "logic": "Extracting truth from a visual representation or raw data.",
    },
    "lawyer": {
        "step_count": 4,
        "labels": ["Concept ID", "Relation", "Evidence / Claim", "Conclusion"],
        "logic": "Claim -> Evidence -> Reasoning (CER).",
    },
}

DEFAULT_SKILLS_BY_BLUEPRINT: dict[str, list[str]] = {
    "solver": [
        "Select correct equation",
        "Extract known values with units",
        "Substitute values into equation",
        "Compute final answer with sig figs",
    ],
    "recipe": [
        "Identify conversion goal",
        "Select conversion factors",
        "Set up dimensional analysis",
        "Compute final answer with sig figs",
    ],
    "architect": [
        "Identify chemical rules/inventory",
        "Draft initial symbolic representation",
        "Refine structure/coefficients",
        "Finalize symbolic answer",
    ],
    "detective": [
        "Extract data from representation",
        "Identify key feature or pattern",
        "Apply chemical concept to data",
        "Draw scientific conclusion",
    ],
    "lawyer": [
        "Identify governing concept",
        "State chemical relationship",
        "Provide evidence/reasoning",
        "State final conclusion",
    ],
}


def get_step_count_for_prompt(blueprint: str) -> int:
    return int(BLUEPRINT_CONFIG.get(blueprint, BLUEPRINT_CONFIG["solver"])["step_count"])


def collect_skills_from_lesson_objectives(lesson_context: dict | None, blueprint: str) -> list[str]:
    """Use lesson objectives as canonical per-step skills, with blueprint fallback."""
    if lesson_context and (objectives := lesson_context.get("objectives")):
        cleaned = [str(x).strip() for x in objectives if str(x).strip()]
        if cleaned:
            return list(dict.fromkeys(cleaned))
    return DEFAULT_SKILLS_BY_BLUEPRINT.get(blueprint, DEFAULT_SKILLS_BY_BLUEPRINT["solver"])


def build_skills_block(skills: list[str]) -> str:
    if not skills:
        return ""
    return (
        "SKILL LIST (use EXACT values for skillUsed): "
        + "; ".join(skills)
        + '\nFor each step include "skillUsed" and choose one item from this list only.'
    )
