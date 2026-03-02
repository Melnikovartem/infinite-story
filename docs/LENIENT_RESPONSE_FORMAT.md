# Lenient Response Format Guide

Instead of requiring strict JSON, the AI can now respond in a flexible key-value format that's much easier to generate and less prone to syntax errors.

## Basic Format

```
field_name: value
another_field: another value
complex_field: value spanning
    multiple lines
    with indentation
```

## Scene Generation Example

```
short_description: A dimly lit tavern at the edge of town
atmosphere: Smoky and tense
time_of_day: Late evening
weather: Rain pattering on the windows

text: The tavern door creaks open. Inside, the smell of ale and smoke fills the air. A few patrons glance up from their drinks, sizing you up carefully. The barkeep polishes a glass with a rag that's seen better days.

characters_present: barkeep, hooded_figure, merchant
locations_present: tavern

choice_1: Approach the bar and order a drink
choice_2: Sit at a corner table and observe
```

## World/Setting Example

```
name: The Kingdom of Aethel
premise: A vast medieval kingdom surrounded by ancient forests
themes: power, duty, mystery, tradition
key_locations: royal capital, deep forests, coastal cities, mountain fortresses
history: Founded 500 years ago by the legendary King Aethel
current_state: Peaceful but with growing tensions at the borders
```

## Character Example

```
name: Lord Thorne
description: A weathered nobleman with silver-streaked hair
personality: Cunning, honorable, but haunted by past mistakes
motivation: Seeking redemption while protecting his lands
background: Former warrior turned statesman, lost his family in war
current_status: Recovering from a political scandal
relationships:
    king: wary ally
    daughter: loving but distant
    rival_lord: bitter enemy
```

## Location Example

```
name: The Crystal Caverns
description: Vast underground chambers filled with glowing crystals
atmosphere: Ethereal and magical
features: crystal formations, hidden chambers, underground lake, ancient ruins
inhabitants: crystal creatures, ancient guardians
history: Sacred site used by the ancient civilization
```

## Choice Generation Example

```
first: Take the mysterious job offer
second: Ask more questions before deciding
third: Decline and continue investigating on your own
```

## Field Name Variations Supported

The parser accepts many variations:

### Scene Fields
- `short_description` = `description` = `scene`
- `text_blocks` = `narrative` = `text`
- `atmosphere` = `mood`
- `time_of_day` = `time`
- `characters_present` = `characters`
- `locations_present` = `locations`
- `choice_1` = `first_choice`
- `choice_2` = `second_choice`

### World Fields
- `name` = `world_name` = `title`
- `premise` = `description`
- `background` = `history`
- `state` = `current_state`
- `locations` = `key_locations`

### Character Fields
- `name` = `character_name`
- `description` = `bio`
- `personality` = `traits`
- `motivation` = `goals`
- `background` = `history`
- `status` = `current_status`

### Location Fields
- `name` = `location_name`
- `description` = `details`
- `mood` = `atmosphere`
- `key_features` = `features`
- `background` = `history`

### Choice Fields
- `choice_1` = `first` = `option1` = `option_1`
- `choice_2` = `second` = `option2` = `option_2`
- `choice_3` = `third` = `option3` = `option_3`

## List Format

Lists can be comma-separated or space-separated:

```
characters_present: barkeep, hooded figure, merchant
themes: power, duty, mystery
features: crystal formations hidden chambers underground lake
```

All will be parsed correctly into arrays.

## Multi-line Values

Indented lines continue the previous value:

```
description: This is a very long description that spans
    multiple lines for clarity. Just indent the continuation
    lines and they'll be joined together properly.
```

## Fallback to JSON

If the AI accidentally generates JSON, the parser will detect and use it:

```json
{
  "short_description": "A tavern scene",
  "atmosphere": "smoky"
}
```

The parser will automatically detect and handle this.

## Benefits

1. **No Syntax Errors**: No brackets, quotes, or escaping to worry about
2. **More Natural**: Reads like a simple outline
3. **Flexible**: Accepts many field name variations
4. **Forgiving**: Falls back to JSON if provided
5. **Easy to Generate**: AI won't struggle with formatting

## Example Prompt to AI

```
Generate the next scene in key-value format:

field_name: value format is easiest - no JSON needed
field_name: value
field_name: multi-line values are supported with
    indentation on continuation lines

I need:
- short_description: Brief scene summary
- atmosphere: Overall mood
- time_of_day: When it happens
- characters_present: Comma-separated character names
- choice_1: First decision option
- choice_2: Second decision option

Use clear field names, separate with colons, and you're done!
```

## Validation

All required fields must be present. The parser will:
- Accept any capitalization (converted to lowercase for matching)
- Handle missing optional fields gracefully
- Return sensible defaults for missing values
- Log warnings for unrecognized fields

