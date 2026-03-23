import React, { useState, useEffect } from 'react';
import { useProgressWebSocket } from '../hooks/useProgressWebSocket';

export default function DownloaderView() {
  const [url, setUrl] = useState('');
  const [format, setFormat] = useState('mp3');
  const [preset, setPreset] = useState('Smart (Auto)');
  const [isProcessing, setIsProcessing] = useState(false);
  const { progress, message: status, setProgress, setMessage: setStatus } = useProgressWebSocket();


  useEffect(() => {
    const handleDownloadEvent = (e) => {
      if (e.detail) {
        setUrl(e.detail);
      }
    };
    window.addEventListener('MUSICPRO_DOWNLOAD', handleDownloadEvent);
    return () => window.removeEventListener('MUSICPRO_DOWNLOAD', handleDownloadEvent);
  }, []);

  const handleDownload = async () => {
    if (!url) return;
    
    setIsProcessing(true);
    setStatus('Inicializando Descarga...');
    setProgress(10);
    
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const resp = await fetch(`${API_BASE}/api/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Bypass-Tunnel-Reminder': 'true'
        },
        body: JSON.stringify({ url, format, preset })
      });


      
      const data = await resp.json();
      
      if (resp.ok) {
        setStatus(`¡Completado! Se descargaron ${data.items.length} pista(s)`);
        setProgress(100);
      } else {
        setStatus(`Error: ${data.message || 'Error desconocido'}`);
        setProgress(0);
      }
    } catch (err) {
      console.error(err);
      setStatus('Falló la conexión al servidor.');
      setProgress(0);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProgress(0), 4000);
    }
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '600px', margin: '0 auto', width: '100%', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      
      <div style={{ textAlign: 'center' }}>
        <h2 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Descarga de Estudio</h2>
        <p style={{ color: 'var(--text-muted)' }}>Pega cualquier enlace de YouTube o video para extraer audio de alta fidelidad.</p>
      </div>

      <div className="glass-card" style={{ width: '100%', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        <div className="form-group">
          <label className="form-label">URL del Video o Playlist</label>
          <input 
            type="text" 
            placeholder="https://youtube.com/watch?v=..." 
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isProcessing}
          />
        </div>

        <div className="flex-row">
          <div className="form-group flex-1">
            <label className="form-label">Formato de Audio</label>
            <select value={format} onChange={(e) => setFormat(e.target.value)} disabled={isProcessing}>
              <option value="mp3">MP3 (Alta Calidad 320kbps)</option>
              <option value="flac">FLAC (Sin Pérdida de Datos)</option>
            </select>
          </div>
          
          <div className="form-group flex-1">
            <label className="form-label">Perfil de Sonido</label>
            <select value={preset} onChange={(e) => setPreset(e.target.value)} disabled={isProcessing}>
              <option value="Smart (Auto)">Restauración Inteligente</option>
              <option value="Studio Hi-Res (Upscale)">Audio Hi-Res (Escalado a 96kHz/24-bit)</option>
              <option value="Bass Boost (Club)">Aumento de Graves (Club)</option>
              <option value="Vocal Clarity">Claridad Vocal y Diálogo</option>
              <option value="Dynamic (Pop/Rock)">Dinámico (Pop/Rock)</option>
            </select>
          </div>
        </div>

        <button 
          className="btn btn-primary" 
          onClick={handleDownload}
          disabled={!url || isProcessing}
          style={{ width: '100%', marginTop: '0.5rem' }}
        >
          {isProcessing ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="spinner" /> Procesando...
            </span>
          ) : (
            "Iniciar Descarga"
          )}
        </button>

      </div>

      {/* Área de estado */}
      <div style={{ width: '100%', textAlign: 'center' }}>
        <div className="progress-container" style={{ opacity: isProcessing || progress > 0 ? 1 : 0, transition: 'opacity 0.3s ease', marginBottom: '8px', height: '8px', background: 'var(--glass-bg)', borderRadius: '4px', overflow: 'hidden' }}>
          <div className="progress-bar" style={{ width: `${Math.max(5, progress)}%`, height: '100%', background: 'var(--primary-glow)', transition: 'width 0.3s ease' }}></div>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', minHeight: '1.2rem' }}>
          {status || (isProcessing ? 'Procesando...' : 'Listo para iniciar')}
        </div>
      </div>
      
    </div>
  );
}
