import { useEffect, useState, useRef } from 'react';

export function useProgressWebSocket() {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const ws = useRef(null);

  useEffect(() => {
    // Determine WS URL from HTTP URL
    const httpUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    // Replace http/https with ws/wss
    const wsProtocol = httpUrl.startsWith('https') ? 'wss' : 'ws';
    const wsUrl = httpUrl.replace(/^https?:\/\//, `${wsProtocol}://`) + '/api/ws/progress';
    
    const connect = () => {
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.percent !== undefined) setProgress(data.percent);
          if (data.message !== undefined) setMessage(data.message);
        } catch (e) {
          console.error("WS Parse error:", e);
        }
      };

      ws.current.onclose = () => {
        // Auto-reconnect if closed
        setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect on unmount
        ws.current.close();
      }
    };
  }, []);

  return { progress, message, setProgress, setMessage };
}
