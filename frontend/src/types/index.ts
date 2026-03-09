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
  id: string;
  user_id: string;
  story_id: string;
  current_segment_id: string;
  visited_segments: string[];
  visited_choices: string[];
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
  start_segment_id?: string;
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

export interface EpisodeInfo {
  number: number;
  segment_in_episode: number;
  tone: string | null;
  arc_id: string | null;
  arc_title?: string | null;
  triggers_transition: boolean;
}

export interface EpisodeSummary {
  id: string;
  episode_number: number;
  arc_id: string | null;
  title: string | null;
  summary: string | null;
  episode_complete: boolean;
  segment_count: number;
  tone: string | null;
}

export interface ArcSummary {
  id: string;
  title: string | null;
  description: string | null;
  is_active: boolean;
  is_finalized: boolean;
  episode_count: number;
  themes: string[];
  central_conflict: string | null;
}

export interface GenerationResponse {
  segment: StorySegment;
  choices: StoryChoice[];
}

export interface StoryListResponse {
  stories: Story[];
}

// ── Story Creation Types ──

export interface CreateStoryRequest {
  story_id: string;
  title: string;
  description: string;
  genre: string;
  world_input?: string;
  first_scene_input?: string;
}

export interface CreationStepUpdate {
  step: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  message: string;
}

export interface CreationJobStatus {
  story_id: string;
  status: 'running' | 'completed' | 'failed';
  current_step: CreationStepUpdate | null;
  steps: CreationStepUpdate[];
  error: string | null;
  result: CreationSummary | null;
}

export interface CreationSummary {
  story_id: string;
  success: boolean;
  error: string | null;
  steps_completed: number;
  steps_total: number;
  summary: {
    factions: number;
    locations: number;
    arcs: number;
    characters: number;
    choices: number;
    has_protagonist: boolean;
    has_magic_system: boolean;
  };
}
