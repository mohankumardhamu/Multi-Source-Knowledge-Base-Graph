import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { DocumentsPage } from './pages/DocumentsPage';
import { DocumentLibraryPage } from './pages/DocumentLibraryPage';
import { SearchPage } from './pages/SearchPage';
import { QAPage } from './pages/QAPage';
import { RoadmapPage } from './pages/RoadmapPage';
import { AdminPage } from './pages/AdminPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="document-library" element={<DocumentLibraryPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="qa" element={<QAPage />} />
          <Route path="roadmap" element={<RoadmapPage />} />
          <Route path="admin" element={<AdminPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
