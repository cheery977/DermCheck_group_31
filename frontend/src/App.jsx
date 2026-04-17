import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Upload from './pages/Upload'
import Results from './pages/Results'
import Portal from './pages/Portal'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/"          element={<Home />} />
            <Route path="/analyse"   element={<Upload />} />
            <Route path="/results/:id" element={<Results />} />
            <Route path="/portal"    element={<Portal />} />
          </Routes>
        </main>
        <footer className="text-center text-xs text-slate-400 py-4 border-t border-slate-200">
          DermCheck is not a medical device. Always consult a qualified healthcare professional.
        </footer>
      </div>
    </BrowserRouter>
  )
}
