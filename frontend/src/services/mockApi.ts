/**
 * Mock API for development/testing without a backend.
 * 
 * Not currently used (USE_MOCK = false in api.ts).
 * Kept for offline development reference.
 */

import type {
  Story,
  StorySegment,
  StoryChoice,
  SessionState,
} from '../types'

// Simulate network latency
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const mockStories: Story[] = [
  {
    id: 'veil_of_thornreach',
    title: 'The Veil of Thornreach',
    description: 'A tale of mystery and discovery in an ancient sanctuary where the protective wards are beginning to fail.',
    genre: 'Fantasy',
    start_segment_id: 'segment_001',
    created_at: '2024-02-28T09:00:00Z',
  },
]

const mockSegments: Record<string, StorySegment> = {
  segment_001: {
    id: 'segment_001',
    story_id: 'veil_of_thornreach',
    short_description: 'The Last Sanctuary',
    atmosphere: 'tense',
    text_blocks: [
      {
        type: 'NARRATOR_DESCRIBING',
        content: 'The ancient trees sway gently in the evening breeze.',
        emotion: null,
        character: null,
      },
      {
        type: 'CHARACTER_SPEECH',
        content: 'The wards are weakening.',
        emotion: 'concerned',
        character: 'Eira',
      },
    ],
  },
  segment_002: {
    id: 'segment_002',
    story_id: 'veil_of_thornreach',
    short_description: 'Into the Veil',
    atmosphere: 'otherworldly',
    text_blocks: [
      {
        type: 'NARRATOR_DESCRIBING',
        content: 'You step forward, your boots crunching on the moss-covered path.',
        emotion: null,
        character: null,
      },
      {
        type: 'CHARACTER_SPEECH',
        content: 'Stay close. The magic here is unstable.',
        emotion: 'cautious',
        character: 'Eira',
      },
    ],
  },
}

const mockChoices: Record<string, StoryChoice[]> = {
  segment_001: [
    {
      id: 'choice_001',
      from_segment_id: 'segment_001',
      to_segment_id: 'segment_002',
      choice_text: 'Investigate the weakening wards with Eira',
      popularity_score: 85,
    },
    {
      id: 'choice_002',
      from_segment_id: 'segment_001',
      to_segment_id: null,
      choice_text: 'Venture into the Veil alone',
      popularity_score: 78,
    },
  ],
  segment_002: [
    {
      id: 'choice_004',
      from_segment_id: 'segment_002',
      to_segment_id: null,
      choice_text: 'Follow the strange lights deeper into the unknown',
      popularity_score: 72,
    },
    {
      id: 'choice_005',
      from_segment_id: 'segment_002',
      to_segment_id: null,
      choice_text: "Ask Eira about her family's connection to the wards",
      popularity_score: 68,
    },
  ],
}

export async function fetchStories() {
  await delay(300)
  return mockStories
}

export async function fetchStoryDetail(storyId: string) {
  await delay(400)
  const story = mockStories.find(s => s.id === storyId)
  if (!story) throw new Error(`Story ${storyId} not found`)

  return {
    ...story,
    start_segment_id: story.start_segment_id,
    characters: [
      {
        id: 'eira',
        story_id: storyId,
        name: 'Eira',
        avatar_shape: 'circle' as const,
        avatar_color: '#FF6B6B',
        description: 'A young mage with a strong connection to the wards',
        background: 'Raised in the sanctuary',
        running_status: [],
      },
    ],
    locations: [
      {
        id: 'thornreach_grove',
        story_id: storyId,
        name: 'Thornreach Grove',
        description: 'Ancient forest sanctuary',
        running_status: [],
      },
    ],
  }
}

export async function fetchSegment(_storyId: string, segmentId: string) {
  await delay(350)
  const segment = mockSegments[segmentId]
  if (!segment) throw new Error(`Segment ${segmentId} not found`)

  const choices = mockChoices[segmentId] || []

  return {
    segment,
    choices: {
      top_2: choices.slice(0, 2),
      all: choices,
    },
  }
}

export async function generateNextScene(
  storyId: string,
  _segmentId: string,
  choiceText: string
) {
  await delay(2000)

  const newSegmentId = `segment_${Date.now()}`
  return {
    segment: {
      id: newSegmentId,
      story_id: storyId,
      short_description: 'A New Path Unfolds',
      text_blocks: [
        {
          type: 'NARRATOR_DESCRIBING' as const,
          content: `The world responds to your choice: "${choiceText}"`,
          emotion: null,
          character: null,
        },
      ],
    },
    choices: {
      top: [
        {
          id: `choice_${Date.now()}_1`,
          from_segment_id: newSegmentId,
          to_segment_id: null,
          choice_text: 'Continue forward with determination',
          generated: true,
        },
        {
          id: `choice_${Date.now()}_2`,
          from_segment_id: newSegmentId,
          to_segment_id: null,
          choice_text: 'Pause and assess the situation',
          generated: true,
        },
      ],
      all: [
        {
          id: `choice_${Date.now()}_1`,
          from_segment_id: newSegmentId,
          to_segment_id: null,
          choice_text: 'Continue forward with determination',
          generated: true,
        },
        {
          id: `choice_${Date.now()}_2`,
          from_segment_id: newSegmentId,
          to_segment_id: null,
          choice_text: 'Pause and assess the situation',
          generated: true,
        },
      ],
    },
  }
}

export async function navigateToChoice(
  _storyId: string,
  _segmentId: string,
  choiceId: string
) {
  await delay(300)

  const choice = Object.values(mockChoices)
    .flat()
    .find(c => c.id === choiceId)

  if (!choice || !choice.to_segment_id) {
    throw new Error('Choice has no destination')
  }

  const segment = mockSegments[choice.to_segment_id]
  if (!segment) throw new Error('Destination segment not found')

  const choices = mockChoices[choice.to_segment_id] || []

  return {
    segment,
    choices: {
      top: choices.slice(0, 2).map(c => ({
        id: c.id,
        from_segment_id: c.from_segment_id,
        to_segment_id: c.to_segment_id,
        choice_text: c.choice_text,
        generated: false,
      })),
      all: choices.map(c => ({
        id: c.id,
        from_segment_id: c.from_segment_id,
        to_segment_id: c.to_segment_id,
        choice_text: c.choice_text,
        generated: false,
      })),
    },
  }
}

export async function saveSession(session: {
  id: string
  story_id: string
  user_id: string
  current_segment_id: string
  visited_segments: string[]
  visited_choices: string[]
}): Promise<void> {
  await delay(200)
  localStorage.setItem(`session_${session.story_id}`, JSON.stringify(session))
}

export async function loadSession(storyId: string, _sessionId: string): Promise<SessionState | null> {
  await delay(150)
  const data = localStorage.getItem(`session_${storyId}`)
  return data ? JSON.parse(data) : null
}

export async function deleteSession(storyId: string, _sessionId: string): Promise<void> {
  await delay(100)
  localStorage.removeItem(`session_${storyId}`)
}

export async function submitReport(
  _storyId: string,
  _segmentId: string,
  _reportType: string,
  _description: string,
  _reporterEmail: string
): Promise<{ report_id: string }> {
  await delay(300)
  return {
    report_id: `report_${Date.now()}`,
  }
}
