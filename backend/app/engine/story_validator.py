"""Story validation and auto-generation service.

Validates story completeness and generates missing components on-demand:
- World description (if missing)
- Story description (if missing)
- Arcs (generates 3 future outlines if no active arcs)
- Characters (parses from existing segments or generates)
- Protagonist (selects or develops one)
"""

import logging
from typing import Dict, List, Optional, Any
import uuid

from app.models.story import Story
from app.models.story_context import StoryContext
from app.models.story_arc import StoryArc
from app.models.story_character import StoryCharacter
from app.models.story_segment import StorySegment
from app.engine.generator import TextGenerator
from app.engine.generators.world_generator import WorldGenerator
from app.engine.generators.arc_generator import ArcGenerator
from app.engine.generators.character_generator import CharacterGenerator
from app.engine.generators.protagonist_selector import ProtagonistSelector

logger = logging.getLogger("infinite_story.engine.story_validator")


class StoryValidator:
    """Validates story completeness and triggers auto-generation of missing pieces."""
    
    def __init__(self, story: Story, generator: Optional[TextGenerator] = None):
        """Initialize the story validator.
        
        Args:
            story: The Story instance to validate
            generator: Optional AI generator for content generation
        """
        self.story = story
        self.generator = generator
        self.validation_report: Dict[str, Any] = {}
    
    async def validate_and_repair(self) -> Dict[str, Any]:
        """Validate story and auto-generate missing pieces.
        
        Validation order (fixes immediately if generation available):
        1. Story description (basic string)
        2. World description (context with fundamental truths + worldbuilding)
        3. Arcs (generates 3 future arc outlines if no active arcs)
        4. Characters (parses from segments or generates if missing)
        5. Protagonist (selects from existing or develops new)
        
        Returns:
            Validation report with status of each component
            
        Raises:
            ValueError: If critical generation fails
        """
        report = {
            'story_id': self.story.id,
            'timestamp': None,
            'validation_results': {},
            'generated': [],
            'errors': []
        }
        
        try:
            logger.info(f"Starting story validation for '{self.story.id}'")
            
            # 1. Validate story description
            await self._validate_story_description()
            report['validation_results']['story_description'] = self.validation_report.get('story_description')
            
            # 2. Validate world description
            await self._validate_world_description()
            report['validation_results']['world_description'] = self.validation_report.get('world_description')
            
            # 3. Validate arcs
            await self._validate_arcs()
            report['validation_results']['arcs'] = self.validation_report.get('arcs')
            
            # 4. Validate characters
            await self._validate_characters()
            report['validation_results']['characters'] = self.validation_report.get('characters')
            
            # 5. Validate protagonist
            await self._validate_protagonist()
            report['validation_results']['protagonist'] = self.validation_report.get('protagonist')
            
            report['generated'] = self.validation_report.get('generated', [])
            
            logger.info(f"Story validation complete. Generated: {report['generated']}")
            return report
            
        except Exception as e:
            logger.error(f"Story validation failed: {e}", exc_info=True)
            raise ValueError(f"Story validation failed: {str(e)}")
    
    async def _validate_story_description(self) -> None:
        """Validate story has a meaningful description."""
        if not self.story.description or len(self.story.description.strip()) < 10:
            logger.warning("Story description is missing or too short")
            
            if self.generator:
                try:
                    desc = await self._generate_story_description()
                    self.story.description = desc
                    self.story.save()
                    self.validation_report['story_description'] = {
                        'status': 'generated',
                        'description': desc[:100] + "..."
                    }
                    self.validation_report.setdefault('generated', []).append('story_description')
                    logger.info("Generated story description")
                except Exception as e:
                    logger.error(f"Failed to generate story description: {e}")
                    raise
            else:
                self.validation_report['story_description'] = {
                    'status': 'missing',
                    'error': 'No generator available'
                }
        else:
            self.validation_report['story_description'] = {
                'status': 'valid',
                'length': len(self.story.description)
            }
    
    async def _validate_world_description(self) -> None:
        """Validate story has world context with fundamental truths and worldbuilding."""
        context = self.story._context
        
        if not context:
            logger.warning("Story context (world description) is missing")
            
            if self.generator:
                try:
                    context = await self._generate_world_context()
                    self.story.add_context(context)
                    context.save()
                    self.validation_report['world_description'] = {
                        'status': 'generated',
                        'truths_count': len(context.fundamental_truths),
                        'worldbuilding_size': len(str(context.worldbuilding))
                    }
                    self.validation_report.setdefault('generated', []).append('world_context')
                    logger.info("Generated world context")
                except Exception as e:
                    logger.error(f"Failed to generate world context: {e}")
                    raise
            else:
                self.validation_report['world_description'] = {
                    'status': 'missing',
                    'error': 'No generator available'
                }
        else:
            self.validation_report['world_description'] = {
                'status': 'valid',
                'truths_count': len(context.fundamental_truths),
                'worldbuilding_size': len(str(context.worldbuilding))
            }
    
    async def _validate_arcs(self) -> None:
        """Validate story has active arcs. Generate 3 future arc outlines if none exist."""
        # Check for active arcs
        active_arcs = self._get_active_arcs()
        
        if active_arcs:
            self.validation_report['arcs'] = {
                'status': 'valid',
                'active_count': len(active_arcs),
                'arc_ids': [arc.id for arc in active_arcs]
            }
        else:
            logger.warning("No active arcs found in story")
            
            if self.generator:
                try:
                    arcs = await self._generate_future_arcs(count=3)
                    self.validation_report['arcs'] = {
                        'status': 'generated',
                        'count': len(arcs),
                        'arc_outlines': [
                            {
                                'id': arc.id,
                                'title': arc.title,
                                'premise': arc.premise,
                                'central_conflict': arc.central_conflict
                            }
                            for arc in arcs
                        ]
                    }
                    self.validation_report.setdefault('generated', []).append('arcs')
                    logger.info(f"Generated {len(arcs)} future arc outlines")
                except Exception as e:
                    logger.error(f"Failed to generate arcs: {e}")
                    raise
            else:
                self.validation_report['arcs'] = {
                    'status': 'missing',
                    'error': 'No generator available'
                }
    
    async def _validate_characters(self) -> None:
        """Validate story has characters. Parse from segments or generate if missing."""
        existing_chars = list(self.story._characters.values())
        
        if existing_chars:
            self.validation_report['characters'] = {
                'status': 'valid',
                'count': len(existing_chars),
                'character_ids': [c.id for c in existing_chars]
            }
        else:
            logger.warning("No characters found in story")
            
            # Try to parse from existing segments
            parsed_chars = await self._parse_characters_from_segments()
            
            if parsed_chars:
                self.validation_report['characters'] = {
                    'status': 'parsed_from_segments',
                    'count': len(parsed_chars),
                    'characters': [c.id for c in parsed_chars]
                }
                self.validation_report.setdefault('generated', []).append('characters_parsed')
                logger.info(f"Parsed {len(parsed_chars)} characters from segments")
            else:
                # Generate from world + arcs
                if self.generator:
                    try:
                        chars = await self._generate_initial_characters()
                        self.validation_report['characters'] = {
                            'status': 'generated',
                            'count': len(chars),
                            'characters': [c.id for c in chars]
                        }
                        self.validation_report.setdefault('generated', []).append('characters_generated')
                        logger.info(f"Generated {len(chars)} initial characters")
                    except Exception as e:
                        logger.error(f"Failed to generate characters: {e}")
                        raise
                else:
                    self.validation_report['characters'] = {
                        'status': 'missing',
                        'error': 'No generator available'
                    }
    
    async def _validate_protagonist(self) -> None:
        """Validate story has a protagonist selected."""
        # Check if first segment has protagonist
        if self.story.start_segment_id:
            start_seg = self.story.get_segment(self.story.start_segment_id)
            if start_seg and start_seg.protagonist_id:
                self.validation_report['protagonist'] = {
                    'status': 'valid',
                    'protagonist_id': start_seg.protagonist_id,
                    'protagonist_name': self._get_character_name(start_seg.protagonist_id)
                }
                return
        
        # No protagonist found
        logger.warning("No protagonist defined in story")
        
        if self.generator and self.story._characters:
            try:
                protag = await self._select_or_develop_protagonist()
                
                # Store in start segment
                if self.story.start_segment_id:
                    start_seg = self.story.get_segment(self.story.start_segment_id)
                    if start_seg:
                        start_seg.protagonist_id = protag.id
                        start_seg.save()
                
                self.validation_report['protagonist'] = {
                    'status': 'selected',
                    'protagonist_id': protag.id,
                    'protagonist_name': protag.name
                }
                self.validation_report.setdefault('generated', []).append('protagonist_selected')
                logger.info(f"Selected protagonist: {protag.name}")
            except Exception as e:
                logger.error(f"Failed to select protagonist: {e}")
                raise
        else:
            self.validation_report['protagonist'] = {
                'status': 'missing',
                'error': 'No generator available or no characters'
            }
    
    # =========================================================================
    # PRIVATE GENERATION METHODS
    # =========================================================================
    
    async def _generate_story_description(self) -> str:
        """Generate a story description based on world and arcs."""
        # TODO: AI prompt to generate story description
        return f"A story in the world of {self.story.title}"
    
    async def _generate_world_context(self) -> StoryContext:
        """Generate world context with fundamental truths and worldbuilding."""
        generator = WorldGenerator(self.generator)
        context = await generator.generate_world_context(
            story=self.story,
            user_input=""  # TODO: Could come from user
        )
        return context
    
    async def _generate_future_arcs(self, count: int = 3) -> List[StoryArc]:
        """Generate high-level outlines for future arcs."""
        generator = ArcGenerator(self.story, self.generator)
        arcs = await generator.generate_future_arcs(
            count=count,
            user_input=""  # TODO: Could come from user
        )
        return arcs
    
    async def _parse_characters_from_segments(self) -> List[StoryCharacter]:
        """Parse characters from existing segment text."""
        generator = CharacterGenerator(self.story, self.generator)
        chars = await generator.parse_characters_from_segments()
        return chars
    
    async def _generate_initial_characters(self) -> List[StoryCharacter]:
        """Generate initial characters based on world and arcs."""
        generator = CharacterGenerator(self.story, self.generator)
        chars = await generator.generate_initial_characters(
            count=3,
            user_input=""  # TODO: Could come from user
        )
        return chars
    
    async def _select_or_develop_protagonist(self) -> StoryCharacter:
        """Select best character as protagonist or develop a new one."""
        selector = ProtagonistSelector(self.story, self.generator)
        protag = await selector.select_or_develop_protagonist(user_choice=None)
        return protag
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_active_arcs(self) -> List[StoryArc]:
        """Get all active arcs (those with segments)."""
        active = []
        
        # Check all segments to find which arcs have content
        for segment in self.story._segments.values():
            if segment.arc_id:
                try:
                    arc = StoryArc.load(self.story.id, segment.arc_id)
                    if arc and arc.id not in [a.id for a in active]:
                        active.append(arc)
                except:
                    pass
        
        return active
    
    def _get_character_name(self, char_id: str) -> str:
        """Get character name by ID."""
        char = self.story.get_character(char_id)
        return char.name if char else char_id
