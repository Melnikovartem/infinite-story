import React from 'react'
import { Card } from './Card'
import { CharacterAvatar } from './CharacterAvatar'
import { AvatarShape } from '../types'

export interface TextBlock {
  type: 'NARRATOR_DESCRIBING' | 'CHARACTER_SPEECH' | 'CHARACTER_THOUGHT' | 'ACTION'
  content: string
  emotion?: string | null
  character?: string | null
}

interface Character {
  id: string
  name: string
  avatar_shape: AvatarShape
  avatar_color: string
  status: 'present' | 'absent' | 'mentioned'
  emotion: string
}

interface Location {
  name: string
  description: string
  atmosphere?: string
}

interface SceneContentProps {
  title: string
  textBlocks: TextBlock[]
  characters: Record<string, Character>
  location: Location
  wordCount?: number
}

const textBlockStyles = {
  NARRATOR_DESCRIBING: 'text-neutral-800 italic',
  CHARACTER_SPEECH: 'text-neutral-900 font-medium',
  CHARACTER_THOUGHT: 'text-neutral-700 italic',
  ACTION: 'text-neutral-800',
}

export const SceneContent: React.FC<SceneContentProps> = ({
  title,
  textBlocks,
  characters,
  location,
  wordCount = 0,
}) => {
  const presentCharacters = Object.values(characters).filter(
    (c) => c.status === 'present'
  )

  return (
    <div className="space-y-lg">
      {/* Scene Title */}
      <div className="space-y-md">
        <h2 className="text-3xl font-bold text-neutral-900">
          {title}
        </h2>

        {/* Location Info */}
        <Card className="bg-blue-50 border border-blue-200 space-y-sm">
          <div className="flex items-start gap-md">
            <span className="text-2xl flex-shrink-0">📍</span>
            <div className="flex-1">
              <h4 className="font-semibold text-neutral-900">
                {location.name}
              </h4>
              <p className="text-sm text-neutral-700">
                {location.description}
              </p>
              {location.atmosphere && (
                <p className="text-xs text-neutral-600 mt-sm">
                  Atmosphere: {location.atmosphere}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Present Characters */}
        {presentCharacters.length > 0 && (
          <Card className="bg-purple-50 border border-purple-200 space-y-md">
            <h4 className="font-semibold text-neutral-900">
              Characters Present
            </h4>
            <div className="flex flex-wrap gap-md">
              {presentCharacters.map((character) => (
                <div
                  key={character.id}
                  className="flex flex-col items-center gap-sm"
                >
                  <CharacterAvatar
                    shape={character.avatar_shape}
                    color={character.avatar_color}
                    name={character.name}
                    size="sm"
                  />
                  <div className="text-center">
                    <p className="text-xs font-medium text-neutral-900">
                      {character.name}
                    </p>
                    {character.emotion && (
                      <p className="text-xs text-neutral-600">
                        {character.emotion}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Story Content */}
      <Card className="space-y-md">
        <div className="prose prose-sm max-w-none">
          {textBlocks.map((block, idx) => {
            const style = textBlockStyles[block.type]

            return (
              <div key={idx} className="space-y-md">
                {block.type === 'CHARACTER_SPEECH' && block.character ? (
                  <div className="border-l-4 border-primary pl-md">
                    <p className={`text-sm ${style}`}>
                      <strong>{block.character}:</strong> "{block.content}"
                    </p>
                  </div>
                ) : block.type === 'CHARACTER_THOUGHT' && block.character ? (
                  <div className="border-l-4 border-secondary pl-md">
                    <p className={`text-sm ${style}`}>
                      <em>{block.character}'s thought: {block.content}</em>
                    </p>
                  </div>
                ) : block.type === 'ACTION' ? (
                  <div className="border-l-4 border-warning pl-md">
                    <p className={`text-sm ${style}`}>
                      <em>{block.content}</em>
                    </p>
                  </div>
                ) : (
                  <p className={`text-base leading-relaxed ${style}`}>
                    {block.content}
                  </p>
                )}
              </div>
            )
          })}
        </div>

        {wordCount > 0 && (
          <div className="pt-md border-t border-neutral-200 text-xs text-neutral-600">
            {wordCount} words
          </div>
        )}
      </Card>
    </div>
  )
}
