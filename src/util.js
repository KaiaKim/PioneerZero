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
    if (!user_info) {
        return;
    }

    console.log("USER INFO:", user_info);
    
    const message = {
        action: 'authenticate_guest',
        user_info: user_info
    };
    ws.send(JSON.stringify(message));
}

