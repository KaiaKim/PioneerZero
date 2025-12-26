// Global variables

// Helper functions for game_id in localStorage
function getGameId() {
    return localStorage.getItem('game_id');
}

function setGameId(gameId) {
    if (gameId) {
        localStorage.setItem('game_id', gameId);
    } else {
        localStorage.removeItem('game_id');
    }
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
