function viewMain() {   
    document.querySelector('.selection-screen').style.display = 'none';
    document.querySelector('.game-screen').style.display = 'block';
    document.querySelector('.floor-3d').style.display = 'block';
    document.querySelector('.results-container').style.display = 'none';
}

function viewResults() {
    document.querySelector('.floor-3d').style.display = 'none';
    document.querySelector('.results-container').style.display = 'block';
}

function viewSelection() {
    document.querySelector('.game-screen').style.display = 'none';
    document.querySelector('.selection-screen').style.display = 'block';
}

function clearChat(){
    const chatLog = document.getElementById('chat-log');
    if (chatLog) {
        chatLog.innerHTML = '';
    }
}

function loadChat(sender, time, content, isSystem) {
    const chatLog = document.getElementById('chat-log');
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    if (isSystem) {
        messageDiv.classList.add('system');
    }
    
    const headerDiv = document.createElement('div');
    headerDiv.classList.add('chat-message-header');
    
    const nameSpan = document.createElement('span');
    nameSpan.classList.add('chat-message-name');
    nameSpan.textContent = sender;
    
    const timeSpan = document.createElement('span');
    timeSpan.classList.add('chat-message-time');
    timeSpan.textContent = time;
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('chat-message-content');
    contentDiv.textContent = content;
    
    headerDiv.appendChild(nameSpan);
    headerDiv.appendChild(timeSpan);
    messageDiv.appendChild(headerDiv);
    messageDiv.appendChild(contentDiv);
    
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function loadTokens(characters) {
    // Remove all elements with the 'token' class from the DOM
    document.querySelectorAll('.token').forEach(token => token.remove());
    // Create new tokens for each character
    characters.forEach(character => {
        const cellId = character.pos;
        const cell = Array.from(document.querySelectorAll('.cell')).find(c => c.textContent.trim() === cellId);

        const token = document.createElement('img');
        token.alt = character.name;
        token.src = character.token_image;
        token.classList.add('token');
        cell.appendChild(token);
    });
}
