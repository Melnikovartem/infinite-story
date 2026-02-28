# API Contracts - Infinite Story Engine

This document defines all API endpoints, request/response formats, and data structures. **Use this as the source of truth for all API work.**

---

## Base Information

- **Base URL**: `http://localhost:8000/api`
- **Method**: REST with JSON
- **Content-Type**: `application/json`
- **CORS**: Enabled for frontend origin
- **Authentication**: None (MVP)

---

## Data Structures

### StorySegment

Represents a scene in the story.

```json
{
  "id": "segment_001",
  "story_id": "veil_of_thornreach",
  "title": "The Last Sanctuary",
  "content": "The ancient trees sway gently in the evening breeze...",
  "text_blocks": [
    {
      "type": "NARRATOR_DESCRIBING",
      "content": "The ancient trees sway...",
      "emotion": null,
      "character": null
    },
    {
      "type": "CHARACTER_SPEECH",
      "content": "The wards are weakening.",
      "emotion": "concerned",
      "character": "eira"
    }
  ],
  "character_states": {
    "eira": {
      "name": "Eira",
      "emotion": "concerned",
      "status": "present"
    },
    "brother_cellen": {
      "name": "Brother Cellen",
      "emotion": "determined",
      "status": "present"
    }
  },
  "location_state": {
    "name": "Thornreach Grove",
    "description": "Ancient forest sanctuary",
    "atmosphere": "tense"
  },
  "is_generated": true,
  "created_at": "2024-02-28T10:30:00Z",
  "word_count": 450
}
```

### StoryChoice

Represents a player decision point.

```json
{
  "id": "choice_001",
  "story_id": "veil_of_thornreach",
  "from_segment_id": "segment_001",
  "to_segment_id": "segment_002",
  "choice_text": "Investigate the weakening wards with Eira and Brother Cellen",
  "popularity_score": 85,
  "is_custom": false,
  "created_at": "2024-02-28T10:30:00Z"
}
```

### StoryCharacter

Represents a character in the story.

```json
{
  "id": "eira",
  "story_id": "veil_of_thornreach",
  "name": "Eira",
  "description": "A young mage with strong connection to the wards",
  "avatar_shape": "circle",
  "avatar_color": "#FF6B6B",
  "background": "Raised in the sanctuary, trained since childhood",
  "running_status": [
    {
      "segment_id": "segment_001",
      "emotion": "concerned",
      "status": "present",
      "notes": "Worried about weakening wards"
    },
    {
      "segment_id": "segment_002",
      "emotion": "determined",
      "status": "present",
      "notes": "Decided to investigate the Veil"
    }
  ]
}
```

### StoryLocation

Represents a location in the story.

```json
{
  "id": "thornreach_grove",
  "story_id": "veil_of_thornreach",
  "name": "Thornreach Grove",
  "description": "Ancient forest sanctuary where the story begins",
  "atmosphere": "mystical",
  "running_status": [
    {
      "segment_id": "segment_001",
      "atmosphere": "tense",
      "notes": "The wards are weakening"
    },
    {
      "segment_id": "segment_002",
      "atmosphere": "mysterious",
      "notes": "Strange activity near the Veil"
    }
  ]
}
```

### StoryContext

Represents worldbuilding and rules.

```json
{
  "id": "world_rules",
  "story_id": "veil_of_thornreach",
  "rules": [
    "The Veil separates the sanctuary from the outside world",
    "Magic users can sense disturbances in the wards",
    "The Memory Weaver is an ancient, mysterious being"
  ],
  "fundamental_truths": [
    "The sanctuary has existed for 300 years",
    "Most residents have never seen outside the Veil",
    "The wards have held perfectly... until now"
  ]
}
```

### Story

Top-level story container.

```json
{
  "id": "veil_of_thornreach",
  "title": "The Veil of Thornreach",
  "description": "A tale of mystery and discovery in an ancient sanctuary",
  "author": "Story Creator",
  "start_segment_id": "segment_001",
  "created_at": "2024-02-28T09:00:00Z"
}
```

### Session State

Represents a player's current game session.

```json
{
  "story_id": "veil_of_thornreach",
  "current_segment_id": "segment_005",
  "visited_segments": [
    "segment_001",
    "segment_002",
    "segment_003",
    "segment_005"
  ],
  "scene_counter": 5,
  "start_time": "2024-02-28T14:00:00Z",
  "last_updated": "2024-02-28T14:25:30Z"
}
```

---

## Endpoints

### 1. Get All Stories

**Endpoint**: `GET /stories`

**Description**: List all available stories.

**Response**: 
```json
{
  "stories": [
    {
      "id": "veil_of_thornreach",
      "title": "The Veil of Thornreach",
      "description": "A tale of mystery and discovery",
      "author": "Story Creator",
      "created_at": "2024-02-28T09:00:00Z"
    },
    {
      "id": "story_2",
      "title": "Another Story",
      "description": "...",
      "author": "...",
      "created_at": "..."
    }
  ]
}
```

**Status Codes**:
- `200 OK` - Success

---

### 2. Get Story Details

**Endpoint**: `GET /stories/{story_id}`

**Description**: Get story metadata and start segment.

**Path Parameters**:
- `story_id` (string, required): Story ID (e.g., `veil_of_thornreach`)

**Response**:
```json
{
  "story": {
    "id": "veil_of_thornreach",
    "title": "The Veil of Thornreach",
    "description": "A tale of mystery and discovery",
    "author": "Story Creator",
    "start_segment_id": "segment_001",
    "created_at": "2024-02-28T09:00:00Z"
  },
  "start_segment": {
    "id": "segment_001",
    "title": "The Last Sanctuary",
    "content": "The ancient trees sway gently...",
    "text_blocks": [...],
    "character_states": {...},
    "location_state": {...},
    "is_generated": false,
    "created_at": "2024-02-28T09:00:00Z",
    "word_count": 450
  },
  "characters": [
    {
      "id": "eira",
      "name": "Eira",
      "avatar_shape": "circle",
      "avatar_color": "#FF6B6B",
      "description": "..."
    },
    {
      "id": "brother_cellen",
      "name": "Brother Cellen",
      "avatar_shape": "square",
      "avatar_color": "#4ECDC4",
      "description": "..."
    }
  ],
  "locations": [
    {
      "id": "thornreach_grove",
      "name": "Thornreach Grove",
      "description": "Ancient forest sanctuary",
      "atmosphere": "mystical"
    }
  ]
}
```

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Story doesn't exist

---

### 3. Get Story Segment

**Endpoint**: `GET /segments/{segment_id}`

**Description**: Get a specific segment with its choices.

**Path Parameters**:
- `segment_id` (string, required): Segment ID

**Query Parameters**:
- `story_id` (string, required): Parent story ID

**Response**:
```json
{
  "segment": {
    "id": "segment_001",
    "story_id": "veil_of_thornreach",
    "title": "The Last Sanctuary",
    "content": "The ancient trees sway...",
    "text_blocks": [...],
    "character_states": {...},
    "location_state": {...},
    "is_generated": true,
    "created_at": "2024-02-28T10:30:00Z",
    "word_count": 450
  },
  "choices": {
    "top_2": [
      {
        "id": "choice_001",
        "choice_text": "Investigate the weakening wards",
        "popularity_score": 85,
        "is_custom": false
      },
      {
        "id": "choice_002",
        "choice_text": "Venture into The Veil",
        "popularity_score": 78,
        "is_custom": false
      }
    ],
    "all": [
      {
        "id": "choice_001",
        "choice_text": "Investigate the weakening wards",
        "popularity_score": 85,
        "is_custom": false
      },
      {
        "id": "choice_002",
        "choice_text": "Venture into The Veil",
        "popularity_score": 78,
        "is_custom": false
      },
      {
        "id": "choice_003",
        "choice_text": "Speak with the elders",
        "popularity_score": 62,
        "is_custom": false
      }
    ]
  },
  "scene_counter": {
    "scene_number": 3,
    "start_time": "2024-02-28T14:00:00Z",
    "elapsed_seconds": 1530
  }
}
```

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Segment doesn't exist

---

### 4. Generate Next Scene (Custom Choice)

**Endpoint**: `POST /segments/{segment_id}/next`

**Description**: Generate next scene from a custom player choice.

**Path Parameters**:
- `segment_id` (string, required): Current segment ID

**Request Body**:
```json
{
  "story_id": "veil_of_thornreach",
  "choice_text": "Ask Nyx about the Memory Weaver's whereabouts",
  "context": {
    "previous_segments_count": 5,
    "include_character_details": true,
    "include_location_details": true,
    "include_worldbuilding": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "new_segment": {
    "id": "segment_006",
    "story_id": "veil_of_thornreach",
    "title": "Nyx's Revelation",
    "content": "Nyx's eyes glow softly...",
    "text_blocks": [...],
    "character_states": {...},
    "location_state": {...},
    "is_generated": true,
    "created_at": "2024-02-28T10:45:00Z",
    "word_count": 520
  },
  "new_choices": [
    {
      "id": "choice_004",
      "from_segment_id": "segment_006",
      "to_segment_id": null,
      "choice_text": "Follow Nyx's guidance",
      "popularity_score": 0,
      "is_custom": false
    },
    {
      "id": "choice_005",
      "from_segment_id": "segment_006",
      "to_segment_id": null,
      "choice_text": "Question Nyx's motives",
      "popularity_score": 0,
      "is_custom": false
    }
  ],
  "generation_time_ms": 3420
}
```

**Status Codes**:
- `201 Created` - Scene generated successfully
- `400 Bad Request` - Invalid request
- `404 Not Found` - Segment doesn't exist
- `500 Internal Server Error` - Generation failed

---

### 5. Navigate to Existing Choice

**Endpoint**: `POST /segments/{segment_id}/choice/{choice_id}`

**Description**: Navigate to an existing choice's destination.

**Path Parameters**:
- `segment_id` (string, required): Current segment ID
- `choice_id` (string, required): Choice to navigate to

**Request Body**:
```json
{
  "story_id": "veil_of_thornreach"
}
```

**Response**:
```json
{
  "success": true,
  "segment": {
    "id": "segment_002",
    "story_id": "veil_of_thornreach",
    "title": "Into the Veil",
    "content": "You step forward...",
    "text_blocks": [...],
    "character_states": {...},
    "location_state": {...},
    "is_generated": true,
    "created_at": "2024-02-28T10:35:00Z",
    "word_count": 480
  },
  "choices": {
    "top_2": [...],
    "all": [...]
  }
}
```

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Segment or choice doesn't exist
- `400 Bad Request` - Choice has no destination

---

### 6. Save Session State

**Endpoint**: `POST /sessions/save`

**Description**: Save current game session.

**Request Body**:
```json
{
  "story_id": "veil_of_thornreach",
  "current_segment_id": "segment_005",
  "visited_segments": ["segment_001", "segment_002", "segment_003", "segment_005"],
  "scene_counter": 5,
  "start_time": "2024-02-28T14:00:00Z"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Session saved successfully",
  "saved_at": "2024-02-28T14:25:30Z"
}
```

**Status Codes**:
- `200 OK` - Session saved
- `400 Bad Request` - Invalid data

---

### 7. Load Session State

**Endpoint**: `GET /sessions/{story_id}`

**Description**: Load saved session for a story.

**Path Parameters**:
- `story_id` (string, required): Story ID

**Response**:
```json
{
  "found": true,
  "session": {
    "story_id": "veil_of_thornreach",
    "current_segment_id": "segment_005",
    "visited_segments": ["segment_001", "segment_002", "segment_003", "segment_005"],
    "scene_counter": 5,
    "start_time": "2024-02-28T14:00:00Z",
    "last_updated": "2024-02-28T14:25:30Z"
  }
}
```

**Status Codes**:
- `200 OK` - Session found and returned
- `404 Not Found` - No saved session

---

### 8. Delete Session State

**Endpoint**: `DELETE /sessions/{story_id}`

**Description**: Delete saved session for a story.

**Path Parameters**:
- `story_id` (string, required): Story ID

**Response**:
```json
{
  "success": true,
  "message": "Session deleted"
}
```

**Status Codes**:
- `200 OK` - Session deleted
- `404 Not Found` - No session to delete

---

### 9. Report Content

**Endpoint**: `POST /reports`

**Description**: Report inappropriate content.

**Request Body**:
```json
{
  "story_id": "veil_of_thornreach",
  "segment_id": "segment_005",
  "report_type": "inappropriate_content",
  "description": "This segment contains offensive language",
  "reporter_email": "user@example.com"
}
```

**Response**:
```json
{
  "success": true,
  "report_id": "report_12345",
  "message": "Thank you for your report. We will review it shortly.",
  "created_at": "2024-02-28T14:30:00Z"
}
```

**Status Codes**:
- `201 Created` - Report submitted
- `400 Bad Request` - Missing required fields

---

## Error Response Format

All error responses follow this format:

```json
{
  "error": true,
  "code": "SEGMENT_NOT_FOUND",
  "message": "The requested segment does not exist",
  "status": 404,
  "timestamp": "2024-02-28T14:30:00Z"
}
```

---

## Rate Limiting

No rate limiting for MVP.

---

## CORS

Frontend can make requests from any origin during development. In production, restrict to frontend domain.

---

## Testing the API

### Using cURL

```bash
# Get all stories
curl -X GET http://localhost:8000/api/stories

# Get story details
curl -X GET http://localhost:8000/api/stories/veil_of_thornreach

# Get a segment
curl -X GET "http://localhost:8000/api/segments/segment_001?story_id=veil_of_thornreach"

# Generate next scene
curl -X POST http://localhost:8000/api/segments/segment_001/next \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "veil_of_thornreach",
    "choice_text": "Ask Nyx about the Memory Weaver",
    "context": {
      "previous_segments_count": 5,
      "include_character_details": true,
      "include_location_details": true,
      "include_worldbuilding": true
    }
  }'
```

### Using Frontend (Fetch)

```typescript
// Get all stories
const response = await fetch('http://localhost:8000/api/stories');
const data = await response.json();

// Generate next scene
const response = await fetch(
  'http://localhost:8000/api/segments/segment_001/next',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      story_id: 'veil_of_thornreach',
      choice_text: 'Ask Nyx about the Memory Weaver',
      context: {
        previous_segments_count: 5,
        include_character_details: true,
        include_location_details: true,
        include_worldbuilding: true
      }
    })
  }
);
const newSegment = await response.json();
```

---

## Summary

**Key Points**:
- All data is JSON
- No authentication (MVP)
- Errors have consistent format
- Frontend can start with mocked endpoints using these contracts
- Backend implements exactly to this spec
- All responses include appropriate status codes

---

**Next**: Refer to your specific task file in `developers/dev{N}-*/TASKS.md` for implementation details.
