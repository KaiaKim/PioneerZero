import { useState, useEffect, useRef } from 'react';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [authWs, setAuthWs] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Load user info from localStorage on mount
    const storedUser = localStorage.getItem('user_info');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      } catch (e) {
        console.error('Error parsing stored user:', e);
        localStorage.removeItem('user_info');
      }
    }
  }, []);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    // Close existing connection if any
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Auth WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.type === 'user_added') {
          console.log('User authenticated:', msg.user_info);
          localStorage.setItem('user_info', JSON.stringify(msg.user_info));
          localStorage.setItem('auth_type', 'google');
          setUser(msg.user_info);
        } else if (msg.type === 'google_auth_error' || msg.type === 'auth_error') {
          console.error('Authentication error:', msg.message);
          alert('Authentication failed: ' + msg.message);
          localStorage.removeItem('user_info');
          setUser(null);
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('Auth WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Auth WebSocket disconnected');
      wsRef.current = null;
      setAuthWs(null);
    };

    wsRef.current = ws;
    setAuthWs(ws);
    return ws;
  };

  const loginSIWG = () => {
    // Generate a unique session_id for this OAuth flow
    const sessionId = crypto.randomUUID();
    
    // Open OAuth popup with session_id as query parameter
    const popupUrl = `http://localhost:8000/auth/google/login?session_id=${sessionId}`;
    const popup = window.open(
      popupUrl,
      'google_oauth',
      'width=500,height=600,scrollbars=yes,resizable=yes'
    );

    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
      alert('Popup blocked. Please allow popups for this site.');
      return;
    }

    // Listen for OAuth callback message
    const messageListener = (event) => {
      // Verify origin for security
      if (event.origin !== 'http://localhost:8000') {
        return;
      }

      if (event.data.type === 'oauth_success') {
        const receivedSessionId = event.data.session_id;
        
        // Close popup
        if (popup && !popup.closed) {
          popup.close();
        }
        
        // Remove message listener
        window.removeEventListener('message', messageListener);

        // Connect WebSocket if not already connected
        let ws = wsRef.current;
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          ws = connectWebSocket();
          
          // Wait for WebSocket to open before sending auth message
          const checkConnection = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              clearInterval(checkConnection);
              // Send authentication message with session_id
              ws.send(JSON.stringify({
                action: 'authenticate_google',
                session_id: receivedSessionId
              }));
            } else if (ws && ws.readyState === WebSocket.CLOSED) {
              clearInterval(checkConnection);
              alert('Failed to connect to server. Please try again.');
            }
          }, 100);

          // Timeout after 5 seconds
          setTimeout(() => {
            clearInterval(checkConnection);
            if (ws && ws.readyState !== WebSocket.OPEN) {
              alert('Connection timeout. Please try again.');
            }
          }, 5000);
        } else {
          // Already connected, send immediately
          ws.send(JSON.stringify({
            action: 'authenticate_google',
            session_id: receivedSessionId
          }));
        }
      } else if (event.data.type === 'oauth_error') {
        console.error('OAuth error:', event.data.error);
        alert('Authentication failed: ' + event.data.error);
        
        // Try to close popup (may fail due to COOP, but that's okay)
        try {
          if (popup) {
            popup.close();
          }
        } catch (e) {
          // Ignore COOP errors when closing popup
        }
        
        // Remove message listener
        window.removeEventListener('message', messageListener);
      }
    };

    window.addEventListener('message', messageListener);
    
    // Note: We don't check popup.closed due to Cross-Origin-Opener-Policy restrictions.
    // The message listener will be cleaned up when we receive success/error messages,
    // or on component unmount.
  };

  return { user, loginSIWG };
}
