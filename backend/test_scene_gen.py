#!/usr/bin/env python3
"""Test script to debug scene generation."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.engine.openai_generator import OpenAIGenerator
from app.models.text_types import SceneTextGeneratorResponse

async def test_scene_generation():
    """Test basic scene generation."""
    # Load config
    config = Config.load()

    # Create generator
    generator = OpenAIGenerator(
        api_base=config.generator.base_url,
        api_key=config.generator.api_key,
        model=config.generator.model,
        temperature=config.generator.temperature,
        max_tokens=config.generator.max_tokens
    )

    # Simple test prompt
    user_prompt = """Generate a new scene that follows from the player's choice.

Story Context:
A dark fantasy adventure in Thornreach Grove, the last sanctuary before The Veil.

Current Scene:
The group stands at the edge of Thornreach Grove. The protective wards hum softly.

Player's Choice:
Investigate the weakening wards with Eira and Brother Cellen

Generate the next scene with:
- A brief description (short_description)
- Atmosphere, time of day, weather
- 3-5 text blocks for the scene
- 2 choices for what to do next
"""

    print("Generating scene...")
    print(f"User prompt length: {len(user_prompt)}")
    print("-" * 80)

    response = await generator.generate(
        system_prompt="",
        user_prompt=user_prompt,
        context_type="scene"
    )

    print("\nResponse received:")
    print(f"Has error: {response.error is not None}")
    if response.error:
        print(f"Error: {response.error}")

    if response.raw_response:
        print(f"\nRaw response preview (first 500 chars):")
        print(response.raw_response[:500])
        print("...")

    print("\nResponse attributes:")
    for attr in ['short_description', 'atmosphere', 'text_blocks', 'choice_1', 'choice_2']:
        if hasattr(response, attr):
            val = getattr(response, attr)
            if attr == 'text_blocks':
                print(f"  {attr}: {len(val) if val else 0} blocks")
            else:
                print(f"  {attr}: {str(val)[:100] if val else 'None'}")
        else:
            print(f"  {attr}: MISSING")

if __name__ == "__main__":
    asyncio.run(test_scene_generation())
