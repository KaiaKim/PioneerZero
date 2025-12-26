// Global variables

// Helper functions for game_id from URL parameter
function getGameId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('game_id');
}

function getGuestId() {
    return localStorage.getItem('guest_id');
}

function genGuestId() {
    return localStorage.setItem('guest_id', crypto.randomUUID());
}

function authenticateGuest(guest_id, ws) {
    const message = {
        action: 'authenticate_guest',
        guest_id: guest_id
    };
    ws.send(JSON.stringify(message));

}
