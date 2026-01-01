// Helper functions for game_id from URL parameter
export function getGameId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('game_id');
}

export function getGuestId() {
    return localStorage.getItem('guest_id');
}

export function genGuestId() {
    const guestId = crypto.randomUUID();
    localStorage.setItem('guest_id', guestId);
    return guestId;
}

export function authenticateGuest(guest_id, ws) {
    if (!guest_id) {
        return;
    }
    const message = {
        action: 'authenticate_guest',
        guest_id: guest_id
    };
    ws.send(JSON.stringify(message));
}

