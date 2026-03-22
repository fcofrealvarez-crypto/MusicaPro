import React, { useState } from 'react';

const PlayIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
);

export default function SearchView({ onDownloadRequest }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query) return;
    
    setIsSearching(true);
    setResults([]);
    setError(null);
    
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const resp = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 10 })
      });
      
      const data = await resp.json();
      if (resp.ok) {
        setResults(data.results || []);
      } else {
        setError(data.message || 'La búsqueda falló');
      }
    } catch (err) {
      console.error(err);
      setError('Error de conexión');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', marginBottom: '1rem' }}>Buscar en la Web</h2>
        
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem' }}>
          <input
            type="text"
            placeholder="Busca canciones, artistas, o álbumes..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ flex: 1, padding: '16px 24px', fontSize: '1.1rem', borderRadius: '16px' }}
          />
          <button type="submit" className="btn btn-primary" disabled={isSearching} style={{ borderRadius: '16px', padding: '0 32px' }}>
            {isSearching ? <div className="spinner" /> : "Buscar"}
          </button>
        </form>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '1rem' }}>
        {error && <div style={{ color: 'var(--secondary)', padding: '1rem', background: 'var(--secondary-glow)', borderRadius: '12px' }}>{error}</div>}
        
        {results.map((res, i) => (
          <div key={i} className="glass-card result-card fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
            {res.thumbnail ? (
               <img src={res.thumbnail} alt={res.title} className="result-thumbnail" />
            ) : (
               <div className="result-thumbnail" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                 <PlayIcon />
               </div>
            )}
            
            <div className="result-info">
              <div className="result-title">{res.title}</div>
              <div className="result-meta">
                {res.uploader || 'Artista Desconocido'} • {res.duration ? `${Math.floor(res.duration/60)}:${(res.duration%60).toString().padStart(2, '0')}` : 'Duración Desconocida'}
              </div>
            </div>
            
            <div className="actions">
              <button 
                className="btn btn-secondary btn-icon" 
                title="Descargar Canción"
                onClick={() => onDownloadRequest(res.url)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              </button>
            </div>
          </div>
        ))}

        {!isSearching && results.length === 0 && query && !error && (
           <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
             No se encontraron resultados. Intenta buscar con otros términos.
           </div>
        )}
      </div>
    </div>
  );
}
