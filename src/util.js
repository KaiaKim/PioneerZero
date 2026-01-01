// Helper functions for game_id from URL parameter
export function getGameId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('game_id');
}

export function genGuestId() {
    const guestId = crypto.randomUUID();
    localStorage.setItem('guest_id', guestId);
    return guestId;
}

export function quickAuth(ws) {
    const user_info = localStorage.getItem('user_info');
    if (user_info) {
        console.log("Authenticating with user_info:", user_info);
        const message = {
            action: 'authenticate_user',
            user_info: user_info
        };
        ws.send(JSON.stringify(message));
        return;
    }

    // If no user_info, try guest_id
    const guest_id = localStorage.getItem('guest_id');
    if (guest_id) {
        const message = {
            action: 'authenticate_user',
            guest_id: guest_id
        };
        ws.send(JSON.stringify(message));
        return;
    }
}

