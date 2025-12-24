// Google OAuth login via WebSocket
let authWs = null;
let authResolve = null;

function connectAdminWebSocket() {
    const wsUrl = `ws://localhost:8000/ws`;
    authWs = new WebSocket(wsUrl);



    authWs.onopen = function() {
        console.log('Auth WebSocket connected');

    };
    
    authWs.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        
        if (msg.type === 'google_auth_success') {
            console.log('Google authentication successful:', msg.user_info);
            // Store user info
            localStorage.setItem('google_user', JSON.stringify(msg.user_info));
            localStorage.setItem('auth_type', 'google');
            
            // Update UI
            const app = document.getElementById('app');
            if (app) {
                app.innerHTML = `<h3>Hi ${msg.user_info.name || msg.user_info.email} 👋</h3>`;
            }
            
            // Resolve auth promise if waiting
            if (authResolve) {
                authResolve(msg.user_info);
                authResolve = null;
            }
        } else if (msg.type === 'google_auth_error') {
            console.error('Google authentication error:', msg.message);
            alert('Authentication failed: ' + msg.message);
            
            if (authResolve) {
                authResolve(null);
                authResolve = null;
            }
        } else if (msg.type === 'guest_assigned') {
            // Fallback to guest mode
            localStorage.setItem('guest_number', msg.guest_number);
            console.log(`You joined as Guest ${msg.guest_number}`);
        }
    };
    
    authWs.onerror = function(error) {
        console.error('Auth WebSocket error:', error);
        if (authResolve) {
            authResolve(null);
            authResolve = null;
        }
    };
    
    authWs.onclose = function(event) {
        console.log('Auth WebSocket disconnected');
        authWs = null;
    };
}

function loginSIWG() {
    // Open Google OAuth in popup
    const popup = window.open(
        'http://localhost:8000/auth/google/login',
        'google_oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
    );
    
    // Listen for OAuth callback message
    const messageListener = function(event) {
        // Verify origin for security
        if (event.origin !== 'http://localhost:8000') {
            return;
        }
        
        if (event.data.type === 'oauth_success') {
            // Close popup
            if (popup) {
                popup.close();
            }
            
            // Connect WebSocket if not connected
            if (!authWs || authWs.readyState !== WebSocket.OPEN) {
                connectAdminWebSocket();
                
                // Wait for connection to open
                const checkConnection = setInterval(() => {
                    if (authWs && authWs.readyState === WebSocket.OPEN) {
                        clearInterval(checkConnection);
                        // Send token to server via WebSocket
                        authWs.send(JSON.stringify({
                            action: 'authenticate_google',
                            session_id: event.data.token.session_id,
                            access_token: event.data.token.access_token
                        }));
                    }
                }, 100);
            } else {
                // Send token immediately
                authWs.send(JSON.stringify({
                    action: 'authenticate_google',
                    session_id: event.data.token.session_id,
                    access_token: event.data.token.access_token
                }));
            }
            
            // Remove listener
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
    
    // Check if popup was blocked
    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
        alert('Popup blocked. Please allow popups for this site.');
        window.removeEventListener('message', messageListener);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('btn-siwg');
    if (loginBtn) {
        loginBtn.addEventListener('click', loginSIWG);
    }
    
    // Check if already authenticated
    const googleUser = localStorage.getItem('google_user');
    if (googleUser) {
        try {
            const user = JSON.parse(googleUser);
            const app = document.getElementById('app');
            if (app) {
                app.innerHTML = `<h3>Hi ${user.name || user.email} 👋</h3>`;
            }
        } catch (e) {
            console.error('Error parsing stored user:', e);
        }
    }
});
