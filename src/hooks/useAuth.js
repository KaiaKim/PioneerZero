import { useState, useEffect } from 'react';
import { getGuestId, genGuestId, authenticateGuest } from '../util';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [authWs, setAuthWs] = useState(null);

  useEffect(() => { //load user info from localStorage on mount
    // Check if already authenticated
    const googleUser = localStorage.getItem('user_info');
    if (googleUser) {
      try {
        const userData = JSON.parse(googleUser);
        setUser(userData);
      } catch (e) {
        console.error('Error parsing stored user:', e);
      }
    }
  }, []);

  const connectAdminWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Auth WebSocket connected');
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === 'user_added') {
        console.log('User added:', msg.user_info);
        localStorage.setItem('user_info', JSON.stringify(msg.user_info));
        setUser(msg.user_info);
      } else if (msg.type === 'auth_error') {
        console.error('Authentication error:', msg.message);
        alert('Authentication failed: ' + msg.message);
      }
    };

    ws.onerror = (error) => {
      console.error('Auth WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Auth WebSocket disconnected');
      setAuthWs(null);
    };

    setAuthWs(ws);
  };

  const loginSIWG = () => {
    const popup = window.open(
      'http://localhost:8000/auth/google/login',
      'google_oauth',
      'width=500,height=600,scrollbars=yes,resizable=yes'
    );

    const messageListener = (event) => {
      if (event.origin !== 'http://localhost:8000') {
        return;
      }

      if (event.data.type === 'oauth_success') {
        // Use a ref to track the WebSocket instance
        let wsInstance = authWs;
        
        if (!wsInstance || wsInstance.readyState !== WebSocket.OPEN) {
          // Create new connection
          const wsUrl = `ws://localhost:8000/ws`;
          wsInstance = new WebSocket(wsUrl);

          wsInstance.onopen = () => {
            console.log('Auth WebSocket connected for OAuth');
            wsInstance.send(JSON.stringify({
              action: 'authenticate_google',
              session_id: event.data.token.session_id,
              access_token: event.data.token.access_token
            }));
            setAuthWs(wsInstance);
          };

          // Set up other handlers
          wsInstance.onmessage = (e) => {
            const msg = JSON.parse(e.data);
            if (msg.type === 'google_auth_success') {
              localStorage.setItem('user_info', JSON.stringify(msg.user_info));
              localStorage.setItem('auth_type', 'google');
              setUser(msg.user_info);
            } else if (msg.type === 'google_auth_error') {
              alert('Authentication failed: ' + msg.message);
            } else if (msg.type === 'user_added') {
              localStorage.setItem('guest_number', msg.guest_number);
            }
          };

          wsInstance.onerror = (error) => {
            console.error('Auth WebSocket error:', error);
          };

          wsInstance.onclose = () => {
            setAuthWs(null);
          };
        } else {
          // Already connected, send immediately
          wsInstance.send(JSON.stringify({
            action: 'authenticate_google',
            session_id: event.data.token.session_id,
            access_token: event.data.token.access_token
          }));
        }

        window.removeEventListener('message', messageListener);
      } else if (event.data.type === 'oauth_error') {
        console.error('OAuth error:', event.data.error);
        alert('Authentication failed: ' + event.data.error);
        if (popup) {
          popup.close();
        }
        window.removeEventListener('message', messageListener);
      }
    };

    window.addEventListener('message', messageListener);

    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
      alert('Popup blocked. Please allow popups for this site.');
      window.removeEventListener('message', messageListener);
    }
  };

  useEffect(() => { //close websocket on cleanup
    return () => {
      if (authWs && authWs.readyState === WebSocket.OPEN) {
        authWs.close();
      }
    };
  }, [authWs]);

  return { user, loginSIWG };
}

