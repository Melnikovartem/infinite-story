import {
  Story,
  StoryDetail,
  StorySegment,
  StoryChoice,
  SegmentResponse,
  GenerationResponse,
  SessionState,
  StoryListResponse
} from '../types'

// Simulate network latency
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export const mockStories: Story[] = [
  {
    id: 'veil_of_thornreach',
    title: 'The Veil of Thornreach',
    description: 'A tale of mystery and discovery in an ancient sanctuary where the protective wards are beginning to fail.',
    author: 'Story Creator',
    start_segment_id: 'segment_001',
    created_at: '2024-02-28T09:00:00Z'
  },
  {
    id: 'echoes_of_the_forgotten',
    title: 'Echoes of the Forgotten',
    description: 'Journey through the ruins of a lost civilization and uncover secrets buried beneath the sands.',
    author: 'Story Creator',
    start_segment_id: 'segment_100',
    created_at: '2024-02-27T10:30:00Z'
  }
]

export const mockSegments: Record<string, StorySegment> = {
  segment_001: {
    id: 'segment_001',
    story_id: 'veil_of_thornreach',
    title: 'The Last Sanctuary',
    content: 'The ancient trees sway gently in the evening breeze. You stand at the edge of the Thornreach Grove, where the protective Veil shimmers like heat against the sky. For three hundred years, this barrier has kept the sanctuary safe from the chaos beyond. But something has changed. The wards are weakening.',
    text_blocks: [
      {
        type: 'NARRATOR_DESCRIBING',
        content: 'The ancient trees sway gently in the evening breeze.',
        emotion: null,
        character: null
      },
      {
        type: 'CHARACTER_SPEECH',
        content: 'The wards are weakening.',
        emotion: 'concerned',
        character: 'eira'
      },
      {
        type: 'INTERNAL_MONOLOGUE',
        content: 'You can feel it too—a strange disturbance in the air.',
        emotion: 'uneasy',
        character: null
      }
    ],
    character_states: {
      eira: {
        name: 'Eira',
        emotion: 'concerned',
        status: 'present'
      },
      brother_cellen: {
        name: 'Brother Cellen',
        emotion: 'determined',
        status: 'present'
      }
    },
    location_state: {
      name: 'Thornreach Grove',
      description: 'Ancient forest sanctuary',
      atmosphere: 'tense'
    },
    is_generated: false,
    created_at: '2024-02-28T09:00:00Z',
    word_count: 200
  },
  segment_002: {
    id: 'segment_002',
    story_id: 'veil_of_thornreach',
    title: 'Into the Veil',
    content: 'You step forward, your boots crunching on the moss-covered path. Eira walks beside you, her hand outstretched toward the shimmering Veil. The air grows colder as you approach. Brother Cellen follows, chanting words in an ancient tongue. The light refracts strangely as you cross through the barrier.',
    text_blocks: [
      {
        type: 'NARRATOR_DESCRIBING',
        content: 'You step forward, your boots crunching on the moss-covered path.',
        emotion: null,
        character: null
      },
      {
        type: 'CHARACTER_SPEECH',
        content: 'Stay close. The magic here is unstable.',
        emotion: 'cautious',
        character: 'eira'
      }
    ],
    character_states: {
      eira: {
        name: 'Eira',
        emotion: 'cautious',
        status: 'present'
      },
      brother_cellen: {
        name: 'Brother Cellen',
        emotion: 'focused',
        status: 'present'
      }
    },
    location_state: {
      name: 'The Veil',
      description: 'Magical barrier between worlds',
      atmosphere: 'otherworldly'
    },
    is_generated: false,
    created_at: '2024-02-28T09:15:00Z',
    word_count: 180
  }
}

export const mockChoices: Record<string, StoryChoice[]> = {
  segment_001: [
    {
      id: 'choice_001',
      story_id: 'veil_of_thornreach',
      from_segment_id: 'segment_001',
      to_segment_id: 'segment_002',
      choice_text: 'Investigate the weakening wards with Eira and Brother Cellen',
      popularity_score: 85,
      is_custom: false
    },
    {
      id: 'choice_002',
      story_id: 'veil_of_thornreach',
      from_segment_id: 'segment_001',
      to_segment_id: null,
      choice_text: 'Venture into the Veil alone to examine it more closely',
      popularity_score: 78,
      is_custom: false
    },
    {
      id: 'choice_003',
      story_id: 'veil_of_thornreach',
      from_segment_id: 'segment_001',
      to_segment_id: null,
      choice_text: 'Speak with the elders about what this means for the sanctuary',
      popularity_score: 62,
      is_custom: false
    }
  ],
  segment_002: [
    {
      id: 'choice_004',
      story_id: 'veil_of_thornreach',
      from_segment_id: 'segment_002',
      to_segment_id: null,
      choice_text: 'Follow the strange lights deeper into the unknown',
      popularity_score: 72,
      is_custom: false
    },
    {
      id: 'choice_005',
      story_id: 'veil_of_thornreach',
      from_segment_id: 'segment_002',
      to_segment_id: null,
      choice_text: 'Ask Eira about her family\'s connection to the wards',
      popularity_score: 68,
      is_custom: false
    }
  ]
}

export async function fetchStories(): Promise<StoryListResponse> {
  await delay(300)
  return {
    stories: mockStories
  }
}

export async function fetchStoryDetail(storyId: string): Promise<StoryDetail> {
  await delay(400)
  const story = mockStories.find(s => s.id === storyId)
  if (!story) throw new Error(`Story ${storyId} not found`)

  return {
    ...story,
    start_segment: mockSegments[story.start_segment_id],
    characters: [
      {
        id: 'eira',
        name: 'Eira',
        avatar_shape: 'circle',
        avatar_color: '#FF6B6B',
        description: 'A young mage with a strong connection to the wards',
        background: 'Raised in the sanctuary, trained since childhood'
      },
      {
        id: 'brother_cellen',
        name: 'Brother Cellen',
        avatar_shape: 'square',
        avatar_color: '#4ECDC4',
        description: 'An ancient priest who has guarded the sanctuary for decades',
        background: 'Keeper of the old ways and ancient knowledge'
      }
    ],
    locations: [
      {
        id: 'thornreach_grove',
        name: 'Thornreach Grove',
        description: 'Ancient forest sanctuary where the story begins',
        atmosphere: 'mystical'
      }
    ]
  }
}

export async function fetchSegment(_storyId: string, segmentId: string): Promise<SegmentResponse> {
  await delay(350)
  const segment = mockSegments[segmentId]
  if (!segment) throw new Error(`Segment ${segmentId} not found`)

  const choices = mockChoices[segmentId] || []

  return {
    segment,
    choices: {
      top_2: choices.slice(0, 2),
      all: choices
    },
    scene_counter: {
      scene_number: 1,
      start_time: '2024-02-28T14:00:00Z',
      elapsed_seconds: 0
    }
  }
}

export async function generateNextScene(
  storyId: string,
  _segmentId: string,
  choiceText: string
): Promise<GenerationResponse> {
  await delay(2000) // Simulate AI generation time

  const newSegmentId = `segment_${Date.now()}`
  const newSegment: StorySegment = {
    id: newSegmentId,
    story_id: storyId,
    title: 'A New Path Unfolds',
    content: `Following your decision to "${choiceText}", an unexpected turn of events begins to unfold. The world around you shifts, responding to your choice in ways both subtle and profound.`,
    text_blocks: [
      {
        type: 'NARRATOR_DESCRIBING',
        content: `The world responds to your choice: "${choiceText}"`,
        emotion: null,
        character: null
      },
      {
        type: 'ENVIRONMENT_DESCRIPTION',
        content: 'The air crackles with energy, and new possibilities emerge.',
        emotion: null,
        character: null
      }
    ],
    character_states: {},
    location_state: {
      name: 'Unknown Territory',
      description: 'A place shaped by your decisions',
      atmosphere: 'mysterious'
    },
    is_generated: true,
    created_at: new Date().toISOString(),
    word_count: 150
  }

  return {
    success: true,
    new_segment: newSegment,
    new_choices: [
      {
        id: `choice_${Date.now()}_1`,
        choice_text: 'Continue forward with determination',
        popularity_score: 0,
        is_custom: false
      },
      {
        id: `choice_${Date.now()}_2`,
        choice_text: 'Pause and assess the situation',
        popularity_score: 0,
        is_custom: false
      }
    ],
    generation_time_ms: 1800
  }
}

export async function navigateToChoice(
  _storyId: string,
  _segmentId: string,
  choiceId: string
): Promise<SegmentResponse> {
  await delay(300)

  // Find the destination segment
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
      top_2: choices.slice(0, 2),
      all: choices
    },
    scene_counter: {
      scene_number: 2,
      start_time: '2024-02-28T14:00:00Z',
      elapsed_seconds: 600
    }
  }
}

export async function saveSession(session: SessionState): Promise<void> {
  await delay(200)
  localStorage.setItem(`session_${session.story_id}`, JSON.stringify(session))
}

export async function loadSession(storyId: string): Promise<SessionState | null> {
  await delay(150)
  const data = localStorage.getItem(`session_${storyId}`)
  return data ? JSON.parse(data) : null
}

export async function deleteSession(storyId: string): Promise<void> {
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
    report_id: `report_${Date.now()}`
  }
}
