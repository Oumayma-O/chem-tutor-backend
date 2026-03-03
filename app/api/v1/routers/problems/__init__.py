"""
Problems sub-package — all /problems/* endpoints.

  POST /problems/generate          — cache-aware problem delivery (L1/L2/L3)
  POST /problems/navigate          — prev/next through a student's playlist
  POST /problems/validate-step     — check one step answer
  POST /problems/hint              — get a scaffolded hint for a step
  POST /problems/classify-thinking — error classification / Thinking Tracker
  GET  /problems/reference-card    — conceptual fiche de cours for a topic
"""

from fastapi import APIRouter

from app.api.v1.routers.problems import (
    classify,
    generate,
    hints,
    playlist_navigation,
    reference_card,
    validation,
)

router = APIRouter(prefix="/problems")

router.include_router(generate.router)
router.include_router(playlist_navigation.router)
router.include_router(validation.router)
router.include_router(hints.router)
router.include_router(classify.router)
router.include_router(reference_card.router)
