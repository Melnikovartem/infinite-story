"""Lenient parser for AI-generated responses.

Parses flexible text formats from AI without requiring strict JSON.
Supports formats like:
    field: value
    field: value with spaces
    description:
        Multi-line
        text here
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("infinite_story.engine.lenient_parser")


class LenientParser:
    """Parse flexible text formats from AI responses."""
    
    @staticmethod
    def parse_key_value(text: str) -> Dict[str, str]:
        """Parse simple key: value format.
        
        Handles:
        - key: value
        - key: value with multiple words
        - Multi-line values with indentation
        
        Args:
            text: Text to parse
            
        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        lines = text.strip().split('\n')
        current_key = None
        current_value = []
        
        for line in lines:
            # Check if this is a key line (has : and doesn't start with whitespace)
            if ':' in line and not line.startswith((' ', '\t')):
                # Save previous key-value if exists
                if current_key is not None:
                    result[current_key] = ' '.join(current_value).strip()
                
                # Parse new key-value
                parts = line.split(':', 1)
                current_key = parts[0].strip().lower()
                current_value = [parts[1].strip()] if len(parts) > 1 and parts[1].strip() else []
            elif current_key is not None:
                # Continuation of multi-line value
                current_value.append(line.strip())
        
        # Save last key-value
        if current_key is not None:
            result[current_key] = ' '.join(current_value).strip()
        
        return result
    
    @staticmethod
    def parse_list(text: str, separator: str = ',') -> List[str]:
        """Parse comma or custom-separated list.
        
        Args:
            text: Text to parse (e.g., "item1, item2, item3")
            separator: Separator character (default: comma)
            
        Returns:
            List of items
        """
        if not text or not text.strip():
            return []
        
        items = text.split(separator)
        return [item.strip() for item in items if item.strip()]
    
    @staticmethod
    def extract_section(text: str, section_name: str) -> str:
        """Extract a section from text.
        
        Looks for sections like:
        === SECTION NAME ===
        content here
        === NEXT SECTION ===
        
        Args:
            text: Text to search
            section_name: Name of section to extract
            
        Returns:
            Section content or empty string
        """
        # Look for === SECTION NAME === pattern
        pattern = rf'===\s*{re.escape(section_name)}\s*===\s*(.*?)(?===|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean common AI response artifacts.
        
        Removes:
        - Extra whitespace
        - Common prefixes (like "Sure!", "Here's", etc.)
        - Markdown code blocks
        - Trailing punctuation
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove markdown code blocks
        text = re.sub(r'```(?:json|text)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL)
        
        # Remove common AI prefixes
        text = re.sub(r'^(?:Sure!|Here\'s|Here is|Certainly!|Of course!)\s*', '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    @staticmethod
    def extract_json_like(text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON-like structure from text.
        
        Attempts to find and parse JSON objects in the response.
        
        Args:
            text: Text containing potential JSON
            
        Returns:
            Parsed dict or None
        """
        import json
        
        # Try to find JSON object pattern
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
        
        return None
    
    @staticmethod
    def merge_dicts(base: Dict[str, Any], parsed: Dict[str, Any], 
                   key_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Merge parsed values into base dict with optional key mapping.
        
        Args:
            base: Base dictionary with defaults
            parsed: Parsed values (keys might be different)
            key_mapping: Map from parsed key to base key
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        if not key_mapping:
            # Auto-detect keys
            for key, value in parsed.items():
                if key in result:
                    result[key] = value
                # Try snake_case variations
                elif key.replace(' ', '_') in result:
                    result[key.replace(' ', '_')] = value
        else:
            # Use explicit mapping
            for parsed_key, base_key in key_mapping.items():
                if parsed_key in parsed and base_key in result:
                    result[base_key] = parsed[parsed_key]
        
        return result
    
    @staticmethod
    def parse_scene_response(text: str) -> Dict[str, Any]:
        """Parse a scene generation response in flexible format.
        
        Handles multiple formats:
        1. JSON (falls back)
        2. Key-value pairs
        3. Markdown sections
        
        Expected fields:
        - short_description / description
        - text_blocks / narrative
        - atmosphere / mood
        - time_of_day / time
        - weather
        - characters / characters_present
        - locations / locations_present
        - choice_1 / first_choice
        - choice_2 / second_choice
        
        Args:
            text: Response text from AI
            
        Returns:
            Dict with scene fields
        """
        text = LenientParser.clean_text(text)
        
        # Try JSON first
        json_result = LenientParser.extract_json_like(text)
        if json_result:
            logger.debug("Parsed response as JSON")
            return json_result
        
        # Parse as key-value
        parsed = LenientParser.parse_key_value(text)
        logger.debug(f"Parsed response as key-value: {list(parsed.keys())}")
        
        # Map to standard fields
        result = {
            'short_description': None,
            'text_blocks': [],
            'atmosphere': None,
            'time_of_day': None,
            'weather': None,
            'characters_present': [],
            'locations_present': [],
            'choice_1': None,
            'choice_2': None,
        }
        
        # Map common field names
        field_mapping = {
            'description': 'short_description',
            'scene': 'short_description',
            'narrative': 'text_blocks',
            'text': 'text_blocks',
            'mood': 'atmosphere',
            'time': 'time_of_day',
            'characters': 'characters_present',
            'locations': 'locations_present',
            'first_choice': 'choice_1',
            'second_choice': 'choice_2',
        }
        
        for parsed_key, value in parsed.items():
            # Direct match
            if parsed_key in result:
                if parsed_key in ['characters_present', 'locations_present']:
                    result[parsed_key] = LenientParser.parse_list(value)
                elif parsed_key in ['text_blocks']:
                    result[parsed_key] = [{'type': 'narrator_describing', 'content': value}]
                else:
                    result[parsed_key] = value
            # Mapped match
            elif parsed_key in field_mapping:
                target_key = field_mapping[parsed_key]
                if target_key in ['characters_present', 'locations_present']:
                    result[target_key] = LenientParser.parse_list(value)
                elif target_key in ['text_blocks']:
                    result[target_key] = [{'type': 'narrator_describing', 'content': value}]
                else:
                    result[target_key] = value
        
        return result
    
    @staticmethod
    def parse_world_response(text: str) -> Dict[str, Any]:
        """Parse world/setting generation response.
        
        Expected fields:
        - name / world_name
        - premise / description
        - themes
        - key_locations / locations
        - history / background
        - current_state / state
        
        Args:
            text: Response text from AI
            
        Returns:
            Dict with world fields
        """
        text = LenientParser.clean_text(text)
        
        # Try JSON first
        json_result = LenientParser.extract_json_like(text)
        if json_result:
            return json_result
        
        parsed = LenientParser.parse_key_value(text)
        
        result = {
            'name': None,
            'premise': None,
            'themes': [],
            'key_locations': [],
            'history': None,
            'current_state': None,
        }
        
        field_mapping = {
            'world_name': 'name',
            'title': 'name',
            'description': 'premise',
            'background': 'history',
            'state': 'current_state',
            'locations': 'key_locations',
        }
        
        for parsed_key, value in parsed.items():
            if parsed_key in result:
                if parsed_key == 'themes':
                    result[parsed_key] = LenientParser.parse_list(value)
                elif parsed_key == 'key_locations':
                    result[parsed_key] = LenientParser.parse_list(value)
                else:
                    result[parsed_key] = value
            elif parsed_key in field_mapping:
                target_key = field_mapping[parsed_key]
                if target_key in ['themes', 'key_locations']:
                    result[target_key] = LenientParser.parse_list(value)
                else:
                    result[target_key] = value
        
        return result
    
    @staticmethod
    def parse_character_response(text: str) -> Dict[str, Any]:
        """Parse character generation response.
        
        Expected fields:
        - name / character_name
        - description / bio
        - personality / traits
        - motivation / goals
        - background / history
        - current_status / status
        - relationships
        
        Args:
            text: Response text from AI
            
        Returns:
            Dict with character fields
        """
        text = LenientParser.clean_text(text)
        
        # Try JSON first
        json_result = LenientParser.extract_json_like(text)
        if json_result:
            return json_result
        
        parsed = LenientParser.parse_key_value(text)
        
        result = {
            'name': None,
            'description': None,
            'personality': None,
            'motivation': None,
            'background': None,
            'current_status': None,
            'relationships': {},
        }
        
        field_mapping = {
            'character_name': 'name',
            'bio': 'description',
            'traits': 'personality',
            'goals': 'motivation',
            'history': 'background',
            'status': 'current_status',
        }
        
        for parsed_key, value in parsed.items():
            if parsed_key in result:
                if parsed_key == 'relationships':
                    # Try to parse as key-value pairs for relationships
                    result[parsed_key] = LenientParser.parse_key_value(value)
                else:
                    result[parsed_key] = value
            elif parsed_key in field_mapping:
                target_key = field_mapping[parsed_key]
                result[target_key] = value
        
        return result
    
    @staticmethod
    def parse_location_response(text: str) -> Dict[str, Any]:
        """Parse location/setting generation response.
        
        Expected fields:
        - name / location_name
        - description / details
        - atmosphere / mood
        - features / key_features
        - inhabitants
        - history / background
        
        Args:
            text: Response text from AI
            
        Returns:
            Dict with location fields
        """
        text = LenientParser.clean_text(text)
        
        # Try JSON first
        json_result = LenientParser.extract_json_like(text)
        if json_result:
            return json_result
        
        parsed = LenientParser.parse_key_value(text)
        
        result = {
            'name': None,
            'description': None,
            'atmosphere': None,
            'features': [],
            'inhabitants': [],
            'history': None,
        }
        
        field_mapping = {
            'location_name': 'name',
            'details': 'description',
            'mood': 'atmosphere',
            'key_features': 'features',
            'background': 'history',
        }
        
        for parsed_key, value in parsed.items():
            if parsed_key in result:
                if parsed_key in ['features', 'inhabitants']:
                    result[parsed_key] = LenientParser.parse_list(value)
                else:
                    result[parsed_key] = value
            elif parsed_key in field_mapping:
                target_key = field_mapping[parsed_key]
                if target_key in ['features', 'inhabitants']:
                    result[target_key] = LenientParser.parse_list(value)
                else:
                    result[target_key] = value
        
        return result
    
    @staticmethod
    def parse_choice_response(text: str) -> Dict[str, Any]:
        """Parse choice generation response.
        
        Expected fields:
        - choice_1 / first / option1
        - choice_2 / second / option2
        - choice_3 / third / option3 (optional)
        
        Args:
            text: Response text from AI
            
        Returns:
            Dict with choice fields
        """
        text = LenientParser.clean_text(text)
        
        # Try JSON first
        json_result = LenientParser.extract_json_like(text)
        if json_result:
            return json_result
        
        parsed = LenientParser.parse_key_value(text)
        
        result = {
            'choice_1': None,
            'choice_2': None,
            'choice_3': None,
        }
        
        field_mapping = {
            'first': 'choice_1',
            'option1': 'choice_1',
            'option_1': 'choice_1',
            'second': 'choice_2',
            'option2': 'choice_2',
            'option_2': 'choice_2',
            'third': 'choice_3',
            'option3': 'choice_3',
            'option_3': 'choice_3',
        }
        
        for parsed_key, value in parsed.items():
            if parsed_key in result:
                result[parsed_key] = value
            elif parsed_key in field_mapping:
                target_key = field_mapping[parsed_key]
                result[target_key] = value
        
        return result

