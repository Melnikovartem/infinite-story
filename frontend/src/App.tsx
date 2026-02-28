import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { StoryProvider } from './contexts/StoryContext'
import Layout from './components/Layout'
import StoryListPage from './pages/StoryListPage'
import StoryDetailPage from './pages/StoryDetailPage'
import PlayPage from './pages/PlayPage'

function App() {
  return (
    <BrowserRouter>
      <StoryProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<StoryListPage />} />
            <Route path="/story/:storyId" element={<StoryDetailPage />} />
            <Route path="/play/:storyId" element={<PlayPage />} />
          </Routes>
        </Layout>
      </StoryProvider>
    </BrowserRouter>
  )
}

export default App
