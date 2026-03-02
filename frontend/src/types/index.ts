/**
 * Type definitions for Infinite Story Engine
 */

export type AvatarShape = 'square' | 'circle' | 'triangle' | 'diamond' | 'star' | 'pentagon';

export interface StoryCharacter {
  id: string;
  story_id: string;
  name: string;
  description: string;
  avatar_shape: AvatarShape;
  avatar_color: string;
  background: string;
  running_status: CharacterState[];
}

export interface CharacterState {
  segment_id: string;
  emotion: string;
  status: 'present' | 'absent' | 'mentioned';
}

export interface LocationState {
  name: string;
  description: string;
  atmosphere?: string;
}

export interface TextBlock {
  type: 'NARRATOR_DESCRIBING' | 'CHARACTER_SPEECH' | 'CHARACTER_THOUGHT' | 'ACTION';
  content: string;
  emotion?: string | null;
  character?: string | null;
}

export interface StorySegment {
  id: string;
  story_id: string;
  short_description?: string;
  title?: string;
  content?: string;
  text_blocks: TextBlock[];
  character_states?: Record<string, CharacterState & { name: string }>;
  location_state?: LocationState;
  is_generated?: boolean;
  created_at?: string;
  word_count?: number;
  atmosphere?: string;
  time_of_day?: string;
  weather?: string;
  characters_present?: string[];
  locations_present?: string[];
}

export interface StoryChoice {
  id: string;
  story_id?: string;
  from_segment_id: string;
  to_segment_id: string | null;
  choice_text: string;
  popularity_score?: number;
  is_custom?: boolean;
  created_at?: string;
  generated?: boolean;
}

export interface StoryContext {
  id: string;
  story_id: string;
  rules: string[];
  fundamental_truths: string[];
  world_description: string;
}

export interface StoryLocation {
  id: string;
  story_id: string;
  name: string;
  description: string;
  running_status: Array<{
    segment_id: string;
    atmosphere: string;
  }>;
}

export interface Story {
  id: string;
  title: string;
  description: string;
  author?: string;
  genre?: string;
  start_segment_id?: string;
  character_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface SessionState {
  story_id: string;
  current_segment_id: string;
  visited_segments: string[];
  current_choices: StoryChoice[];
  character_states: Record<string, CharacterState & { name: string }>;
  location_state: LocationState;
  created_at: string;
  updated_at: string;
}

export interface PlayerState {
  current_story_id: string | null;
  current_segment_id: string | null;
  visited_segments: string[];
  character_states: Record<string, CharacterState & { name: string }>;
  loading: boolean;
  error: string | null;
}

export interface StoryDetail extends Story {
  author: string;
  genre?: string;
  characters: StoryCharacter[];
  locations: StoryLocation[];
}

export interface SceneCounter {
  total: number;
  current: number;
}

export interface ChoicesResponse {
  top_2: StoryChoice[];
  all: StoryChoice[];
}

export interface SegmentResponse {
  segment: StorySegment;
  choices: ChoicesResponse;
}

export interface GenerationResponse {
  segment: StorySegment;
  choices: StoryChoice[];
}

export interface StoryListResponse {
  stories: Story[];
}
