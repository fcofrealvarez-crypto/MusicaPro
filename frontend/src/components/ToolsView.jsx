import React, { useState, useRef } from 'react';
import { useProgressWebSocket } from '../hooks/useProgressWebSocket';

function FileProcessorCard({ title, description, apiEndpoint, extraFields, onResult, wsProps }) {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [localStatus, setLocalStatus] = useState('');
  const fileInputRef = useRef(null);
  const [formDataState, setFormDataState] = useState({});

  const status = isProcessing && wsProps ? (wsProps.message || 'Procesando...') : localStatus;
  const progress = isProcessing && wsProps ? Math.max(5, wsProps.progress) : 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setLocalStatus('Por favor selecciona un archivo primero.');
      return;
    }
    
    setIsProcessing(true);
    if(wsProps) wsProps.setProgress(5);
    setLocalStatus('Subiendo archivo al servidor...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Añadir campos adicionales
    Object.keys(formDataState).forEach(key => {
      formData.append(key, formDataState[key]);
    });
    
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const resp = await fetch(`${API_BASE}${apiEndpoint}`, {
        method: 'POST',
        body: formData
      });
      
      if (resp.ok) {
        const blob = await resp.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        
        const disposition = resp.headers.get('Content-Disposition');
        let filename = `procesado_${file.name}`;
        if (disposition && disposition.indexOf('filename=') !== -1) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (matches != null && matches[1]) { 
                filename = matches[1].replace(/['"]/g, '');
            }
        }
        
        onResult(downloadUrl, filename);
        setLocalStatus('¡Éxito! Tu archivo está listo para descargar.');
        if(wsProps) wsProps.setProgress(100);
      } else {
        const err = await resp.json();
        setLocalStatus(`Error: ${err.message || 'El procesamiento falló'}`);
        if(wsProps) wsProps.setProgress(0);
      }
    } catch (err) {
      console.error(err);
      setLocalStatus('Falló la conexión con el servidor.');
      if(wsProps) wsProps.setProgress(0);
    } finally {
      setIsProcessing(false);
      if(wsProps) setTimeout(() => wsProps.setProgress(0), 4000);
    }
  };

  return (
    <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
      <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }} className="gradient-text">{title}</h3>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>{description}</p>
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        
        <div style={{ padding: '1.5rem', border: '2px dashed var(--glass-border)', borderRadius: '12px', textAlign: 'center', cursor: 'pointer', background: file ? 'var(--primary-glow)' : 'transparent', transition: 'all 0.3s' }} onClick={() => fileInputRef.current.click()}>
          <input 
            type="file" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            onChange={(e) => setFile(e.target.files[0])} 
            accept="audio/*"
          />
          {file ? (
            <div style={{ fontWeight: '500', color: 'var(--text-main)' }}>Seleccionado: {file.name}</div>
          ) : (
            <div style={{ color: 'var(--text-muted)' }}>Haz clic para seleccionar un archivo de audio</div>
          )}
        </div>
        
        {extraFields && extraFields(formDataState, setFormDataState)}
        
        <button type="submit" className="btn btn-primary" disabled={!file || isProcessing}>
          {isProcessing ? <><div className="spinner"/> Procesando...</> : "Iniciar Procesamiento"}
        </button>
        
        {/* Progress Bar for Tools */}
        <div style={{ width: '100%', textAlign: 'center' }}>
          <div className="progress-container" style={{ opacity: isProcessing || progress > 0 ? 1 : 0, transition: 'opacity 0.3s ease', marginBottom: '8px', height: '6px', background: 'var(--glass-bg)', borderRadius: '4px', overflow: 'hidden' }}>
            <div className="progress-bar" style={{ width: `${progress}%`, height: '100%', background: 'var(--accent-teal)', transition: 'width 0.3s ease' }}></div>
          </div>
          
          {status && (
            <div style={{ marginTop: '0.2rem', fontSize: '0.9rem', color: isProcessing ? 'var(--text-muted)' : 'var(--text-main)', textAlign: 'center' }}>
              {status}
            </div>
          )}
        </div>
      </form>
    </div>
  );
}

export default function ToolsView() {
  const [downloadLink, setDownloadLink] = useState(null);
  const wsProps = useProgressWebSocket();
  
  const handleResult = (url, filename) => {
    setDownloadLink({url, filename});
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="fade-in" style={{ height: '100%', overflowY: 'auto', paddingRight: '1rem' }}>
      <h2 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Herramientas de Audio</h2>
      
      {downloadLink && (
        <div style={{ background: 'rgba(20, 184, 166, 0.2)', padding: '1rem', borderRadius: '12px', marginBottom: '2rem', border: '1px solid var(--accent-teal)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong>¡Éxito!</strong> Tu archivo fue procesado y se descargó automáticamente.
          </div>
          <button className="btn btn-secondary" onClick={() => handleResult(downloadLink.url, downloadLink.filename)}>Descargar de Nuevo</button>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem' }}>
        
        <FileProcessorCard 
          title="Convertidor de Formato"
          description="Convierte tus audios entre distintos formatos (MP3, FLAC, M4A)"
          apiEndpoint="/api/convert"
          onResult={handleResult}
          wsProps={wsProps}
          extraFields={(state, setState) => (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Formato de Destino</label>
              <select value={state.target_format || 'mp3'} onChange={(e) => setState({...state, target_format: e.target.value})}>
                <option value="mp3">MP3 (Alta Calidad 320kbps)</option>
                <option value="flac">FLAC (Sin Pérdida de Datos)</option>
                <option value="m4a">M4A (AAC)</option>
              </select>
            </div>
          )}
        />
        
        <FileProcessorCard 
          title="Remasterizado Inteligente"
          description="Aplica arreglos dinámicos y ecualización con IA para mejorar audios de baja calidad."
          apiEndpoint="/api/remaster"
          onResult={handleResult}
          wsProps={wsProps}
          extraFields={(state, setState) => (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Perfil de Mejora</label>
              <select value={state.preset || 'Smart (Auto)'} onChange={(e) => setState({...state, preset: e.target.value})}>
                <option value="Smart (Auto)">Restauración Inteligente</option>
                <option value="Studio Hi-Res (Upscale)">Audio Hi-Res (Escalado a 96kHz/24-bit)</option>
                <option value="Bass Boost (Club)">Aumento de Graves (Club)</option>
                <option value="Vocal Clarity">Claridad Vocal y Diálogo</option>
                <option value="Dynamic (Pop/Rock)">Dinámico (Pop/Rock)</option>
              </select>
            </div>
          )}
        />
        
      </div>
      
      <FileProcessorCard 
        title="Editor de Etiquetas (ID3 Metadata)"
        description="Agrega o modifica la información (Título, Artista, Álbum) del archivo de audio."
        apiEndpoint="/api/metadata"
        onResult={handleResult}
        wsProps={wsProps}
        extraFields={(state, setState) => (
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <input type="text" placeholder="Título" value={state.title || ''} onChange={(e) => setState({...state, title: e.target.value})} style={{ flex: '1 1 30%' }} />
            <input type="text" placeholder="Artista" value={state.artist || ''} onChange={(e) => setState({...state, artist: e.target.value})} style={{ flex: '1 1 30%' }} />
            <input type="text" placeholder="Álbum" value={state.album || ''} onChange={(e) => setState({...state, album: e.target.value})} style={{ flex: '1 1 30%' }} />
          </div>
        )}
      />
      
    </div>
  );
}
