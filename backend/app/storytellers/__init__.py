"""Storyteller system - narrative voice personas for story generation."""

from .registry import (
    Storyteller,
    get_all_storytellers,
    get_storyteller,
    get_default_storyteller,
    get_storyteller_or_default,
)

__all__ = [
    "Storyteller",
    "get_all_storytellers",
    "get_storyteller",
    "get_default_storyteller",
    "get_storyteller_or_default",
]
