import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { StoryProvider } from './contexts/StoryContext'
import './styles/globals.css'
import './App.css'
import StoryListPage from './pages/StoryListPage'
import StoryDetailPage from './pages/StoryDetailPage'
import PlayPage from './pages/PlayPage'
import CreateStoryPage from './pages/CreateStoryPage'

function App() {
  return (
    <StoryProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<StoryListPage />} />
          <Route path="/create" element={<CreateStoryPage />} />
          <Route path="/story/:storyId" element={<StoryDetailPage />} />
          <Route path="/play/:storyId" element={<PlayPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </StoryProvider>
  )
}

export default App
