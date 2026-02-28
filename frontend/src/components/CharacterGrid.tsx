import React from 'react'
import { CharacterAvatar } from './CharacterAvatar'
import { Card } from './Card'
import type { AvatarShape } from '../types'

interface Character {
  id: string
  name: string
  description: string
  avatar_shape: AvatarShape
  avatar_color: string
}

interface CharacterGridProps {
  characters: Character[]
  showDescriptions?: boolean
}

export const CharacterGrid: React.FC<CharacterGridProps> = ({
  characters,
  showDescriptions = false,
}) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-lg">
      {characters.map((character) => (
        <Card
          key={character.id}
          className="text-center space-y-md p-md"
        >
          <div className="flex justify-center">
            <CharacterAvatar
              shape={character.avatar_shape}
              color={character.avatar_color}
              name={character.name}
              size="md"
            />
          </div>

          <div>
            <h4 className="font-semibold text-neutral-900">
              {character.name}
            </h4>

            {showDescriptions && (
              <p className="text-xs text-neutral-600 line-clamp-2 mt-sm">
                {character.description}
              </p>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}
