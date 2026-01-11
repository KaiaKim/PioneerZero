// Configuration
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

export function getWebSocketUrl() {
    return `${WS_BASE_URL}/ws`;
}

export function getApiBaseUrl() {
    return API_BASE_URL;
}

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

export function genChatMessage(chatMsg) {
    const isSecret = chatMsg.sort === "secret";
    const isError = chatMsg.sort === "error";
    let sender = chatMsg.sender;
    if (isSecret) sender += " 👁";
    if (isError) sender += " ❌";
    return {
        sender: sender,
        time: chatMsg.time,
        content: chatMsg.content,
        isSystem: chatMsg.sort === "system",
        isSecret: isSecret,
        isError: isError,
        user_id: chatMsg.user_id || null
    };
}
