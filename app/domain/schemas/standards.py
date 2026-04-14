"""Pydantic schemas for curriculum standards (NGSS, AP, SEPs, CCCs)."""

from pydantic import BaseModel


class StandardOut(BaseModel):
    code: str
    framework: str
    title: str | None = None
    description: str | None = None
    category: str | None = None
    is_core: bool = True
