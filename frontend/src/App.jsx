import React, { useState } from 'react';
import DownloaderView from './components/DownloaderView';
import SearchView from './components/SearchView';
import ToolsView from './components/ToolsView';
import LibraryView from './components/LibraryView';

const IconDownload = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
);
const IconSearch = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
);
const IconTools = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>
);
const IconLibrary = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
);

function App() {
  const [activeTab, setActiveTab] = useState('downloader');

  const renderContent = () => {
    switch (activeTab) {
      case 'downloader': return <DownloaderView />;
      case 'search': return <SearchView onDownloadRequest={(url) => {
        setActiveTab('downloader');
        window.dispatchEvent(new CustomEvent('MUSICPRO_DOWNLOAD', { detail: url }));
      }}/>;
      case 'tools': return <ToolsView />;
      case 'library': return <LibraryView />;
      default: return <DownloaderView />;
    }
  };

  return (
    <div className="app-container">
      <header className="app-header glass-panel">
        <div className="logo-container">
          <div className="logo-icon">MP</div>
          <div>
            <h1 style={{fontSize: '1.5rem', lineHeight: '1'}}>MusicPro</h1>
            <span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Edición Web Premium</span>
          </div>
        </div>
        
        <nav className="nav-tabs">
          <div 
            className={`nav-tab ${activeTab === 'downloader' ? 'active' : ''}`}
            onClick={() => setActiveTab('downloader')}
          >
            <IconDownload /> Descargar
          </div>
          <div 
            className={`nav-tab ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            <IconSearch /> Buscar
          </div>
          <div 
            className={`nav-tab ${activeTab === 'tools' ? 'active' : ''}`}
            onClick={() => setActiveTab('tools')}
          >
            <IconTools /> Herramientas
          </div>
          <div 
            className={`nav-tab ${activeTab === 'library' ? 'active' : ''}`}
            onClick={() => setActiveTab('library')}
          >
            <IconLibrary /> Mi Biblioteca
          </div>
        </nav>
      </header>
      
      <main className="main-content glass-panel">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
