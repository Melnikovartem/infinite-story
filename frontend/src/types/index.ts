export interface TextBlock {
  type: 'NARRATOR_DESCRIBING' | 'CHARACTER_SPEECH' | 'ENVIRONMENT_DESCRIPTION' | 'INTERNAL_MONOLOGUE';
  content: string;
  emotion?: string | null;
  character?: string | null;
}

export interface CharacterState {
  name: string;
  emotion: string;
  status: 'present' | 'absent' | 'deceased';
}

export interface LocationState {
  name: string;
  description: string;
  atmosphere: string;
}

export interface StorySegment {
  id: string;
  story_id: string;
  title: string;
  content: string;
  text_blocks: TextBlock[];
  character_states: Record<string, CharacterState>;
  location_state: LocationState;
  is_generated: boolean;
  created_at: string;
  word_count: number;
}

export interface StoryChoice {
  id: string;
  story_id?: string;
  from_segment_id?: string;
  to_segment_id?: string | null;
  choice_text: string;
  popularity_score: number;
  is_custom: boolean;
}

export interface ChoicesResponse {
  top_2: StoryChoice[];
  all: StoryChoice[];
}

export interface StoryCharacter {
  id: string;
  name: string;
  avatar_shape: 'square' | 'circle' | 'triangle' | 'diamond' | 'star' | 'pentagon';
  avatar_color: string;
  description: string;
  background?: string;
}

export interface StoryLocation {
  id: string;
  name: string;
  description: string;
  atmosphere: string;
}

export interface Story {
  id: string;
  title: string;
  description: string;
  author: string;
  start_segment_id: string;
  created_at: string;
}

export interface StoryDetail extends Story {
  start_segment: StorySegment;
  characters: StoryCharacter[];
  locations: StoryLocation[];
}

export interface SessionState {
  story_id: string;
  current_segment_id: string;
  visited_segments: string[];
  scene_counter: number;
  start_time: string;
  last_updated: string;
}

export interface SceneCounter {
  scene_number: number;
  start_time: string;
  elapsed_seconds: number;
}

export interface SegmentResponse {
  segment: StorySegment;
  choices: ChoicesResponse;
  scene_counter: SceneCounter;
}

export interface GenerationResponse {
  success: boolean;
  new_segment: StorySegment;
  new_choices: StoryChoice[];
  generation_time_ms: number;
}

export interface StoryListResponse {
  stories: Story[];
}
