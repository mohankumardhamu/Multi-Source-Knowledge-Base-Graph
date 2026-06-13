import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { DocumentsPage } from './pages/DocumentsPage';
import { SearchPage } from './pages/SearchPage';
import { QAPage } from './pages/QAPage';
import { RoadmapPage } from './pages/RoadmapPage';
import { AdminPage } from './pages/AdminPage';
import { CallbackPage } from './pages/CallbackPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="callback" element={<CallbackPage />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="documents" element={<ProtectedRoute><DocumentsPage /></ProtectedRoute>} />
          <Route path="search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
          <Route path="qa" element={<ProtectedRoute><QAPage /></ProtectedRoute>} />
          <Route path="roadmap" element={<ProtectedRoute><RoadmapPage /></ProtectedRoute>} />
          <Route path="admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
