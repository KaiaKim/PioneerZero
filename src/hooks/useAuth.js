import { useState, useEffect, useRef } from 'react';
import { genGuestId, quickAuth } from '../util';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [authWs, setAuthWs] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    connectAuthWebSocket();

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectAuthWebSocket = (skipQuickAuth = false) => {
    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);
    let guest_id = null;

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
    } else {
      guest_id = genGuestId();
    }

    ws.onopen = () => {
      console.log('Auth WebSocket connected');
      if (!skipQuickAuth) {
        quickAuth(ws);
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.type === 'auth_success') {
          console.log('User authenticated:', msg.user_info);
          localStorage.setItem('user_info', JSON.stringify(msg.user_info));
          setUser(msg.user_info);
        } else if (msg.type === 'auth_error') {
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

  const googleLogin = () => {
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

      // Only process OAuth messages (success or error)
      if (event.data.type !== 'oauth_success' && event.data.type !== 'oauth_error') {
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

        // Close existing connection if any (we need a fresh connection for Google auth)
        const existingWs = wsRef.current;
        if (existingWs && existingWs.readyState === WebSocket.OPEN) {
          console.warn('Closing existing WebSocket connection for Google auth');
          existingWs.close();
        }
        
        // Create new connection for Google auth (skip quickAuth to avoid double authentication)
        const ws = connectAuthWebSocket(true);
        
        // Wait for WebSocket to open before sending auth message
        const checkConnection = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            clearInterval(checkConnection);
            // Send authentication message with session_id
            ws.send(JSON.stringify({
              action: 'google_login',
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
    
    // Cleanup: Monitor popup and remove listener if closed manually
    const checkPopup = setInterval(() => {
      if (popup && popup.closed) {
        clearInterval(checkPopup);
        window.removeEventListener('message', messageListener);
      }
    }, 500);

    // Cleanup after 5 minutes (timeout for OAuth flow)
    setTimeout(() => {
      clearInterval(checkPopup);
      window.removeEventListener('message', messageListener);
    }, 5 * 60 * 1000);
  };

  const googleLogout = () => {
    localStorage.removeItem('user_info');
    setUser(null);
  };

  return { user, googleLogin, googleLogout };
}
