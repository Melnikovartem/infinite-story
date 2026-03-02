# API Reference

Base URL: `http://localhost:8000/api`

All requests and responses use JSON. No authentication (MVP). CORS enabled for development.

---

## Endpoints

### GET /stories

List all available stories.

**Response** `200`:
```json
{
  "stories": [
    {
      "id": "veil_of_thornreach",
      "title": "The Veil of Thornreach",
      "description": "A tale of mystery and discovery",
      "author": "Story Creator",
      "created_at": "2024-02-28T09:00:00Z"
    }
  ]
}
```

### GET /stories/{story_id}

Get story metadata, start segment, characters, and locations.

**Response** `200`:
```json
{
  "story": {
    "id": "veil_of_thornreach",
    "title": "The Veil of Thornreach",
    "description": "...",
    "author": "Story Creator",
    "start_segment_id": "segment_001",
    "created_at": "..."
  },
  "start_segment": {
    "id": "segment_001",
    "title": "The Last Sanctuary",
    "content": "...",
    "text_blocks": [...],
    "character_states": {...},
    "location_state": {...},
    "is_generated": false,
    "word_count": 450
  },
  "characters": [
    { "id": "eira", "name": "Eira", "avatar_shape": "circle", "avatar_color": "#FF6B6B", "description": "..." }
  ],
  "locations": [
    { "id": "thornreach_grove", "name": "Thornreach Grove", "description": "...", "atmosphere": "mystical" }
  ]
}
```

### GET /segments/{segment_id}?story_id={story_id}

Get a segment with its choices, grouped into top 2 and all.

**Response** `200`:
```json
{
  "segment": {
    "id": "segment_001",
    "story_id": "veil_of_thornreach",
    "title": "The Last Sanctuary",
    "content": "...",
    "text_blocks": [
      { "type": "NARRATOR_DESCRIBING", "content": "...", "emotion": null, "character": null },
      { "type": "CHARACTER_SPEECH", "content": "The wards are weakening.", "emotion": "concerned", "character": "eira" }
    ],
    "character_states": {...},
    "location_state": {...},
    "is_generated": true,
    "word_count": 450
  },
  "choices": {
    "top_2": [
      { "id": "choice_001", "choice_text": "Investigate the weakening wards", "popularity_score": 85, "is_custom": false },
      { "id": "choice_002", "choice_text": "Venture into The Veil", "popularity_score": 78, "is_custom": false }
    ],
    "all": [...]
  },
  "scene_counter": {
    "scene_number": 3,
    "start_time": "2024-02-28T14:00:00Z",
    "elapsed_seconds": 1530
  }
}
```

### POST /segments/{segment_id}/next

Generate next scene from a custom choice (triggers AI generation).

**Request**:
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

**Response** `201`:
```json
{
  "success": true,
  "new_segment": {
    "id": "segment_006",
    "title": "Nyx's Revelation",
    "text_blocks": [...],
    "character_states": {...},
    "location_state": {...},
    "is_generated": true,
    "word_count": 520
  },
  "new_choices": [
    { "id": "choice_004", "from_segment_id": "segment_006", "to_segment_id": null, "choice_text": "Follow Nyx's guidance" },
    { "id": "choice_005", "from_segment_id": "segment_006", "to_segment_id": null, "choice_text": "Question Nyx's motives" }
  ],
  "generation_time_ms": 3420
}
```

### POST /segments/{segment_id}/choice/{choice_id}

Navigate to an existing choice's destination.

**Request**: `{ "story_id": "veil_of_thornreach" }`

**Response** `200`: Same shape as GET /segments/{segment_id} (segment + choices).

### POST /sessions/save

Save current game session.

**Request**:
```json
{
  "story_id": "veil_of_thornreach",
  "current_segment_id": "segment_005",
  "visited_segments": ["segment_001", "segment_002", "segment_005"],
  "scene_counter": 5,
  "start_time": "2024-02-28T14:00:00Z"
}
```

**Response** `200`: `{ "success": true, "message": "Session saved successfully", "saved_at": "..." }`

### GET /sessions/{story_id}

Load saved session. Returns `{ "found": true, "session": {...} }` or `404`.

### DELETE /sessions/{story_id}

Delete saved session. Returns `{ "success": true, "message": "Session deleted" }` or `404`.

### POST /reports

Report inappropriate content.

**Request**:
```json
{
  "story_id": "veil_of_thornreach",
  "segment_id": "segment_005",
  "report_type": "inappropriate_content",
  "description": "...",
  "reporter_email": "user@example.com"
}
```

**Response** `201`: `{ "success": true, "report_id": "report_12345", "message": "..." }`

---

## Error Format

All errors follow this shape:

```json
{
  "error": true,
  "code": "SEGMENT_NOT_FOUND",
  "message": "The requested segment does not exist",
  "status": 404,
  "timestamp": "2024-02-28T14:30:00Z"
}
```

## Data Structures

### StorySegment
Represents a scene. Contains `text_blocks` (array of `TextBlock`), `character_states`, `location_state`, and metadata.

### StoryChoice
An edge connecting two segments via `from_segment_id` and `to_segment_id`. `to_segment_id=null` means destination not yet generated.

### StoryCharacter
Character with `avatar_shape`, `avatar_color`, `background`, and `running_status` (array of state snapshots per segment).

### StoryLocation
Location with `atmosphere`, `description`, and `running_status` history.

### StoryContext
Worldbuilding: `rules` (array of strings) and `fundamental_truths` (array of strings).

### Session
Player state: `current_segment_id`, `visited_segments`, `scene_counter`, timestamps.
