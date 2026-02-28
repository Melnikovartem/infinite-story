import './CharacterAvatar.css'

interface CharacterAvatarProps {
  shape: 'square' | 'circle' | 'triangle' | 'diamond' | 'star' | 'pentagon'
  color: string
  size?: 'small' | 'medium' | 'large'
}

export default function CharacterAvatar({ shape, color, size = 'medium' }: CharacterAvatarProps) {
  const renderShape = () => {
    switch (shape) {
      case 'square':
        return <div className="shape square" style={{ backgroundColor: color }} />
      case 'circle':
        return <div className="shape circle" style={{ backgroundColor: color }} />
      case 'triangle':
        return <div className="shape triangle" style={{ borderBottomColor: color }} />
      case 'diamond':
        return <div className="shape diamond" style={{ backgroundColor: color }} />
      case 'star':
        return <div className="shape star" style={{ backgroundColor: color }} />
      case 'pentagon':
        return <div className="shape pentagon" style={{ backgroundColor: color }} />
      default:
        return <div className="shape circle" style={{ backgroundColor: color }} />
    }
  }

  return (
    <div className={`character-avatar ${size}`}>
      {renderShape()}
    </div>
  )
}
