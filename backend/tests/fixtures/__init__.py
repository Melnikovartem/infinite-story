"""Test fixtures for the infinite story application.

This package provides reusable test fixtures for creating test stories,
characters, locations, segments, and other game objects.

Modules:
    story_builders: Helper functions for building complete test stories
    mock_generators: Mock generators for testing without API calls
"""

from .story_builders import (
    create_test_story_with_segments,
    create_test_story_with_choices,
    create_test_story_with_characters,
    create_branching_story,
    create_story_with_multiple_characters,
)

from .mock_generators import (
    MockTextGenerator,
    MockGeneratorWithErrors,
    MockCharacterGenerator,
    create_mock_response,
)

__all__ = [
    # Story builders
    "create_test_story_with_segments",
    "create_test_story_with_choices",
    "create_test_story_with_characters",
    "create_branching_story",
    "create_story_with_multiple_characters",
    # Mock generators
    "MockTextGenerator",
    "MockGeneratorWithErrors",
    "MockCharacterGenerator",
    "create_mock_response",
]
